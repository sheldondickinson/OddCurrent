"""Single-process API with OIDC, scoped sessions, and outbound device transport."""
import asyncio
import json
import mimetypes
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import urlparse

from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import Config
from .protocol import Ack, Claim, Invite, Lighting, Maintenance, Telemetry
from .store import Store, digest

ROOT = Path(__file__).resolve().parents[1]

def create_app(config: Config):
    config.validate()
    # Minimal Linux images may not include an OS MIME database for WebP.
    mimetypes.add_type('image/webp', '.webp')
    app = FastAPI(title='OddCurrent', docs_url=None, redoc_url=None, openapi_url=None)
    store = Store(config.database)
    app.state.store = store
    app.state.config = config
    connections: dict[str, tuple[WebSocket, str, float]] = {}
    app.state.connections = connections
    rate = defaultdict(deque)
    app.add_middleware(SessionMiddleware, secret_key=config.session_key, session_cookie='oc_oauth',
                       https_only=not config.demo, same_site='lax', max_age=600)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[urlparse(config.public_origin).hostname,'127.0.0.1'], www_redirect=False)
    oauth = OAuth()
    if config.oidc_issuer:
        oauth.register('owner', client_id=config.oidc_client_id, client_secret=config.oidc_client_secret,
                       server_metadata_url=config.oidc_issuer.rstrip('/') + '/.well-known/openid-configuration',
                       client_kwargs={'scope': 'openid profile', 'code_challenge_method': 'S256'})

    def limit(key, max_calls=30):
        now = time.time()
        if len(rate) > 2048:
            for old in list(rate):
                if not rate[old] or rate[old][-1] < now - 60:
                    del rate[old]
            if len(rate) > 2048:
                raise HTTPException(429, 'Please try again shortly')
        q = rate[key]
        while q and q[0] < now - 60:
            q.popleft()
        if len(q) >= max_calls:
            raise HTTPException(429, 'Please try again shortly')
        q.append(now)

    def session(request):
        token = request.cookies.get('oc_session', '')
        found = store.one('SELECT * FROM sessions WHERE hash=? AND expires>?', (digest(token), time.time()))
        if not found:
            raise HTTPException(401, 'Sign in or accept an invitation')
        return found

    def csrf(request, who):
        if request.headers.get('origin') != config.public_origin:
            raise HTTPException(403, 'Origin rejected')
        if not secrets.compare_digest(request.headers.get('x-csrf-token', ''), who['csrf']):
            raise HTTPException(403, 'Request token rejected')

    def authorised(device, who, owner=False):
        row = store.one('SELECT * FROM devices WHERE id=?', (device,))
        if not row:
            raise HTTPException(404, 'Device not found')
        is_owner = who['role'] == 'owner' and row['owner'] == who['subject']
        is_admin = who['role'] == 'admin' and who['subject'] in config.admin_subjects
        is_guest = who['role'] == 'guest' and who['device'] == device
        if not is_owner and not is_admin and (owner or not is_guest):
            raise HTTPException(403, 'This lamp has not been shared with you')
        return row

    def administrator(request):
        who = session(request)
        if who['role'] != 'admin' or who['subject'] not in config.admin_subjects:
            raise HTTPException(403, 'Administrator access required')
        return who

    def cookie(response, token):
        response.set_cookie('oc_session', token, secure=not config.demo, httponly=True,
                            samesite='lax', max_age=43200, path='/')
        return response

    def device_view(row, role):
        last_seen = row['last_seen']
        if config.demo and row['id'] in connections:
            last_seen = time.time()  # simulator heartbeat, explicitly demo-only
            store.execute('UPDATE devices SET last_seen=? WHERE id=?', (last_seen, row['id']))
        online = row['id'] in connections and last_seen is not None and time.time() - last_seen < 45
        reported = json.loads(row['reported'])
        if role != 'admin':
            reported.pop('local_ip', None)
        return {'id': row['id'], 'name': 'David' if row['profile'] == 'david-v1' else row['profile'],
                'profile': row['profile'], 'role': role, 'online': online,
                'last_seen': last_seen, 'reported': reported, 'desired': json.loads(row['desired']),
                'demo': config.demo, 'update_available': False, 'update_status': 'hardware-release-gate'}

    @app.middleware('http')
    async def protections(request, call_next):
        if config.demo and request.client.host not in ('127.0.0.1', '::1', 'localhost', 'testclient'):
            return FileResponse(ROOT / 'web/denied.html', status_code=403)
        # Limit body before JSON parsing. Proxy must impose the same (or smaller) limit.
        if request.method in ('POST', 'PUT', 'PATCH'):
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 4096:
                    return JSONResponse({'detail':'Request too large'}, status_code=413)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers['Permissions-Policy'] = 'microphone=(), camera=(), geolocation=()'
        if request.url.path.startswith(('/api', '/auth')):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        # Do not echo sensitive claim or invitation inputs in validation responses.
        return JSONResponse({'detail':'Invalid request fields'}, status_code=422)

    @app.get('/healthz')
    def health():
        store.one('SELECT 1')
        return {'ok': True, 'service': 'oddcurrent', 'mode': 'demo' if config.demo else 'production'}

    @app.get('/auth/login')
    async def login(request: Request):
        if not config.oidc_issuer:
            raise HTTPException(503, 'Sign-in provider is not configured')
        return await oauth.owner.authorize_redirect(request, config.public_origin + '/auth/callback')

    @app.get('/auth/callback')
    async def callback(request: Request):
        try:
            token = await oauth.owner.authorize_access_token(request)
            user = token.get('userinfo')
            # Authlib validates signed ID token, issuer/audience/nonce/expiry against discovery + JWKS.
            if not token.get('id_token') or not user or user.get('iss') != config.oidc_issuer or not user.get('sub'):
                raise ValueError('invalid subject')
            identity = config.oidc_issuer + '|' + user['sub']
        except Exception:
            request.session.clear()
            raise HTTPException(401, 'Sign-in could not be verified')
        request.session.clear()
        old = request.cookies.get('oc_session', '')
        store.execute('DELETE FROM sessions WHERE hash=?', (digest(old),))
        token, _ = store.session(subject=identity,role='admin' if identity in config.admin_subjects else 'owner')
        return cookie(RedirectResponse('/admin' if identity in config.admin_subjects else '/', status_code=303), token)

    @app.get('/api/session')
    def current(request: Request):
        who = session(request)
        return {'role': who['role'], 'csrf': who['csrf'], 'demo': config.demo}

    @app.post('/api/logout')
    def logout(request: Request):
        who = session(request); csrf(request, who)
        store.execute('DELETE FROM sessions WHERE hash=?', (who['hash'],))
        res = RedirectResponse('/', status_code=303)
        res.delete_cookie('oc_session')
        return res

    @app.get('/api/devices')
    def devices(request: Request):
        who = session(request)
        if who['role']=='admin' and who['subject'] in config.admin_subjects:
            rows=store.all('SELECT * FROM devices ORDER BY id')
        else:
            rows = store.all('SELECT * FROM devices WHERE owner=?' if who['role'] == 'owner' else 'SELECT * FROM devices WHERE id=?',
                             (who['subject'] if who['role'] == 'owner' else who['device'],))
        return [device_view(x, who['role']) for x in rows]

    @app.get('/api/devices/{device}')
    def detail(device: str, request: Request):
        who = session(request)
        return device_view(authorised(device, who), who['role'])

    @app.get('/admin')
    def admin_page(request: Request):
        if not request.cookies.get('oc_session'):
            return RedirectResponse('/auth/login', status_code=303)
        administrator(request)
        return FileResponse(ROOT / 'web/admin.html')

    @app.get('/api/admin/devices')
    def admin_devices(request: Request):
        administrator(request)
        result=[]
        for row in store.all('SELECT * FROM devices ORDER BY id'):
            view=device_view(row, 'admin')
            view['claimed']=row['owner'] is not None
            view['guest_count']=store.one("SELECT COUNT(*) AS n FROM sessions WHERE device=? AND role='guest' AND expires>?", (row['id'],time.time()))['n']
            view['recent_commands']=store.all('SELECT id,seq,status,expires,payload FROM commands WHERE device=? ORDER BY seq DESC LIMIT 10', (row['id'],))
            for command in view['recent_commands']:
                command['payload']=json.loads(command['payload'])
                if command['status']=='pending' and command['expires']<time.time(): command['status']='expired'
            view['events']=store.all('SELECT at,kind FROM events WHERE device=? ORDER BY id DESC LIMIT 20',(row['id'],))
            result.append(view)
        return result

    @app.post('/api/admin/devices/{device}/actions')
    async def admin_action(device: str, data: Maintenance, request: Request):
        who=administrator(request);csrf(request,who);row=authorised(device,who)
        limit(('maintenance',who['hash']),30)
        reported=json.loads(row['reported']);live=connections.get(device)
        if not live or not row['last_seen'] or time.time()-row['last_seen']>=45:
            raise HTTPException(409,'Lamp offline; nothing queued')
        if reported.get('management_protocol')!=1:
            raise HTTPException(409,'This firmware does not support remote maintenance')
        if data.action in ('identify','locate_pixel') and not reported.get('lighting_ready'):
            raise HTTPException(409,'Lighting setup is not enabled')
        if data.action=='locate_pixel' and data.index>=reported.get('body_count',0):
            raise HTTPException(422,'Body pixel index is outside the reported output')
        cmd=store.command(device,data.model_dump(exclude_none=True),capability='maintenance')
        cmd['session']=live[1]
        try:
            await asyncio.wait_for(live[0].send_json(cmd),timeout=2)
        except Exception:
            store.execute('UPDATE commands SET status=? WHERE id=?',('disconnected',cmd['id']))
            raise HTTPException(409,'Connection lost; nothing queued')
        store.event(device,'admin_'+data.action)
        return {'id':cmd['id'],'status':'pending','expires':cmd['expires']}

    @app.post('/api/devices/{device}/claim')
    def claim(device: str, data: Claim, request: Request):
        who = session(request); csrf(request, who)
        limit(('claim', who['hash']), 5)
        if who['role'] not in ('owner','admin') or not store.claim(device, data.code, who['subject']):
            raise HTTPException(403, 'Claim code invalid or already used')
        store.event(device, 'claimed')
        return {'claimed': True}

    @app.post('/api/devices/{device}/commands')
    async def command(device: str, data: Lighting, request: Request):
        who = session(request); csrf(request, who)
        row = authorised(device, who); limit(('command', who['hash']), 60)
        payload = data.model_dump(exclude_none=True)
        if who['role'] == 'guest' and set(payload) - {'on', 'brightness', 'scene', 'music'}:
            raise HTTPException(403, 'Owner controls only')
        profile = json.loads((ROOT / 'profiles' / (row['profile'] + '.json')).read_text())
        if 'lighting' not in profile['capabilities']:
            raise HTTPException(422, 'Lighting capability unavailable')
        if data.zone:
            zones = {z for output in profile['outputs'] if output['key'] != 'status' for z in output['zones']}
            if data.zone not in zones or not json.loads(row['reported']).get('zones_ready', False):
                raise HTTPException(422, 'Zone needs physical calibration')
        live = connections.get(device)
        if not live or not row['last_seen'] or time.time() - row['last_seen'] >= 45:
            raise HTTPException(409, 'Lamp offline; nothing queued')
        if not json.loads(row['reported']).get('lighting_ready', False):
            raise HTTPException(409, 'Lighting setup is not enabled on this lamp; nothing queued')
        cmd = store.command(device, payload)
        cmd['session'] = live[1]
        try:
            await asyncio.wait_for(live[0].send_json(cmd), timeout=2)
        except Exception:
            store.execute('UPDATE commands SET status=? WHERE id=?', ('disconnected', cmd['id']))
            raise HTTPException(409, 'Connection lost; nothing queued')
        store.event(device, 'command_sent')
        return {'id': cmd['id'], 'status': 'pending', 'expires': cmd['expires']}

    @app.get('/api/devices/{device}/commands/{command_id}')
    def command_status(device: str, command_id: str, request: Request):
        authorised(device, session(request))
        row = store.one('SELECT id,status,expires FROM commands WHERE id=? AND device=?', (command_id, device))
        if not row:
            raise HTTPException(404, 'Command not found')
        if row['status'] == 'pending' and row['expires'] < time.time():
            row['status'] = 'expired'
        return row

    @app.post('/api/devices/{device}/invites')
    def invite(device: str, data: Invite, request: Request):
        who = session(request); csrf(request, who); authorised(device, who, owner=True)
        limit(('invite', who['hash']), 10)
        token = secrets.token_urlsafe(32)
        expires = time.time() + data.hours * 3600
        store.execute('INSERT INTO invites VALUES(?,?,?)', (digest(token), device, expires))
        return {'url': config.public_origin + '/invite#' + token, 'expires': expires}

    @app.post('/api/invites/redeem')
    def redeem(data: Claim, request: Request):
        if request.headers.get('origin') != config.public_origin:
            raise HTTPException(403, 'Origin rejected')
        limit(('redeem', request.client.host), 10)
        with store.lock:
            row = store.one('DELETE FROM invites WHERE hash=? AND expires>? RETURNING *', (digest(data.code), time.time()))
            if not row:
                raise HTTPException(403, 'Invitation expired or revoked')
            token, _ = store.session(device=row['device'], role='guest', hours=min(12, (row['expires']-time.time())/3600))
        res = cookie(RedirectResponse('/d/' + row['device'], status_code=303), token)
        store.event(row['device'], 'guest_invitation_accepted')
        return res

    @app.delete('/api/devices/{device}/guests')
    def revoke_guests(device: str, request: Request):
        who = session(request); csrf(request, who); authorised(device, who, owner=True)
        store.execute('DELETE FROM invites WHERE device=?', (device,))
        store.execute("DELETE FROM sessions WHERE device=? AND role='guest'", (device,))
        store.event(device, 'guest_access_revoked')
        return {'revoked': True}

    @app.get('/api/devices/{device}/events')
    def events(device: str, request: Request):
        authorised(device, session(request), owner=True)
        return store.all('SELECT at,kind FROM events WHERE device=? ORDER BY id DESC LIMIT 50', (device,))

    @app.websocket('/ws/devices/{device}')
    async def device_socket(ws: WebSocket, device: str):
        if ws.query_params or ws.headers.get('origin'):
            await ws.close(1008); return
        row = store.one('SELECT * FROM devices WHERE id=?', (device,))
        auth = ws.headers.get('authorization', '')
        if not row or not auth.startswith('Bearer ') or not secrets.compare_digest(digest(auth[7:]), row['credential_hash']):
            await ws.close(1008); return
        if device in connections:
            await ws.close(1013); return
        await ws.accept()
        nonce = secrets.token_hex(16)
        connections[device] = (ws, nonce, time.time())
        store.event(device, 'connected')
        await ws.send_json({'type': 'hello', 'protocol': 1, 'session': nonce, 'time': int(time.time()), 'heartbeat_s': 15})
        try:
            while True:
                raw = await asyncio.wait_for(ws.receive_text(), timeout=45)
                if len(raw) > 2048:
                    await ws.close(1009); break
                limit(('ws', device), 120)
                msg = json.loads(raw)
                if not isinstance(msg,dict):
                    await ws.close(1008); break
                if msg.get('type') == 'telemetry':
                    info = Telemetry.model_validate(msg).model_dump()
                    store.execute('UPDATE devices SET last_seen=?,reported=? WHERE id=?', (time.time(), json.dumps(info), device))
                    await ws.send_json({'type': 'heartbeat', 'time': int(time.time())})
                elif msg.get('type') == 'ack':
                    ack = Ack.model_validate(msg)
                    changed = store.execute("UPDATE commands SET status=? WHERE id=? AND device=? AND seq=? AND status='pending' AND expires>=?",
                                            (ack.status, ack.id, device, ack.seq, time.time())).rowcount
                    if not changed:
                        await ws.close(1008); break
                    store.event(device, 'command_' + ack.status)
                else:
                    await ws.close(1008); break
        except (WebSocketDisconnect, TimeoutError, ValueError, ValidationError, HTTPException):
            pass
        finally:
            connections.pop(device, None)
            store.execute("UPDATE commands SET status='disconnected' WHERE device=? AND status='pending'", (device,))
            store.event(device, 'disconnected')
            try:
                await ws.close()
            except RuntimeError:
                pass

    if config.demo:
        for i in (1, 2):
            device = f'david-demo-{i:03}'
            if not store.one('SELECT id FROM devices WHERE id=?', (device,)):
                store.register(device, 'david-v1', secrets.token_urlsafe(32), secrets.token_urlsafe(24))
                store.execute('UPDATE devices SET owner=? WHERE id=?', ('local-demo', device))

        @app.post('/api/demo/login')
        def demo_login(request: Request):
            if request.headers.get('origin') != config.public_origin:
                raise HTTPException(403, 'Origin rejected')
            token, _ = store.session(subject='local-demo')
            return cookie(RedirectResponse('/', status_code=303), token)

        # A simulator responds through the same validated API surface; never enabled in production.
        class Simulator:
            async def send_json(self, cmd):
                row = store.one('SELECT reported FROM devices WHERE id=?', (self.device,))
                state = json.loads(row['reported']); state.update(cmd['payload'])
                state.pop('zone', None)
                store.execute('UPDATE devices SET reported=?,last_seen=? WHERE id=?', (json.dumps(state), time.time(), self.device))
                store.execute("UPDATE commands SET status='applied' WHERE id=?", (cmd['id'],))

        @app.post('/api/demo/connect')
        def demo_connect(request: Request):
            who = session(request); csrf(request, who)
            for row in store.all("SELECT * FROM devices WHERE owner='local-demo'"):
                sim = Simulator(); sim.device = row['id']
                connections[row['id']] = (sim, 'simulator', time.time())
                state = {'on': True, 'brightness': 65, 'scene': 'gallery', 'music': False, 'sensitivity': 50,
                         'status_brightness': 5, 'rssi': -53, 'firmware': 'SIMULATOR', 'boot_reason': 'simulation',
                         'reconnects': 0, 'uptime_s': 0, 'zones_ready': False, 'xy_ready': False,
                         'lighting_ready': True, 'hardware_ready': False}
                store.execute('UPDATE devices SET last_seen=?,reported=? WHERE id=?', (time.time(), json.dumps(state), row['id']))
            return {'simulator': True}

    app.mount('/assets', StaticFiles(directory=ROOT / 'web/assets'), name='assets')
    for path in ('/', '/d/{device}', '/pair/{device}', '/invite', '/calibrate'):
        app.add_api_route(path, lambda: FileResponse(ROOT / 'web/index.html'), methods=['GET'])
    return app
