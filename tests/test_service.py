import json
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from server.app import create_app
from server.config import Config
from server.protocol import Lighting
from server.store import digest

ORIGIN='https://lamp.example.invalid'

@pytest.fixture
def setup(tmp_path):
    app=create_app(Config(database=str(tmp_path/'db.sqlite'),public_origin=ORIGIN,
                         oidc_issuer='https://identity.example.invalid/application/o/oddcurrent/',oidc_client_id='test'))
    db=app.state.store
    db.register('david-001','david-v1','a'*48,'c'*24)
    db.register('david-002','david-v1','b'*48,'d'*24)
    owner,csrf=db.session(subject='issuer|owner')
    stranger,stranger_csrf=db.session(subject='issuer|stranger')
    db.claim('david-001','c'*24,'issuer|owner')
    client=TestClient(app,base_url=ORIGIN)
    client.cookies.set('oc_session',owner)
    return app,db,client,owner,csrf,stranger,stranger_csrf

def headers(csrf): return {'Origin':ORIGIN,'X-CSRF-Token':csrf}

def telemetry(**values):
    return dict(type='telemetry',on=True,brightness=65,scene='gallery',music=False,
                rssi=-60,firmware='16.0.1',boot_reason='power_on',reconnects=0,uptime_s=10,
                **({'lighting_ready':True} | values))

def test_online_lamp_without_lighting_setup_cannot_queue_commands(setup):
    app,db,client,owner,csrf,*_=setup
    with client.websocket_connect('wss://lamp.example.invalid/ws/devices/david-001',headers={'Authorization':'Bearer '+'a'*48}) as ws:
        ws.receive_json();ws.send_json(telemetry(lighting_ready=False));ws.receive_json()
        response=client.post('/api/devices/david-001/commands',json={'scene':'blue'},headers=headers(csrf))
        assert response.status_code==409
        assert 'Lighting setup' in response.json()['detail']
        assert db.all('SELECT * FROM commands')==[]

def test_anonymous_and_cross_owner_denied(setup):
    app,db,client,owner,csrf,stranger,stranger_csrf=setup
    client.cookies.clear()
    assert client.get('/api/devices').status_code==401
    client.cookies.set('oc_session',stranger)
    assert client.get('/api/devices/david-001').status_code==403
    assert client.post('/api/devices/david-001/commands',json={'on':True},headers=headers(stranger_csrf)).status_code==403
    assert client.get('/api/devices').json()==[]

def test_claim_one_time_and_static_url_no_authority(setup):
    app,db,client,owner,csrf,*_=setup
    assert client.get('/d/david-002').status_code==200
    assert client.get('/api/devices/david-002').status_code==403
    assert client.post('/api/devices/david-002/claim',json={'code':'wrong-code-xxxxxxx'},headers=headers(csrf)).status_code==403
    assert client.post('/api/devices/david-002/claim',json={'code':'d'*24},headers=headers(csrf)).status_code==200
    assert client.post('/api/devices/david-002/claim',json={'code':'d'*24},headers=headers(csrf)).status_code==403
    assert db.one('SELECT claim_hash FROM devices WHERE id=?',('david-002',))['claim_hash'] is None

def test_csrf_and_offline_no_queue(setup):
    app,db,client,owner,csrf,*_=setup
    assert client.post('/api/devices/david-001/commands',json={'on':True}).status_code==403
    assert client.post('/api/devices/david-001/commands',json={'on':True},headers={**headers(csrf),'Origin':'https://evil.invalid'}).status_code==403
    assert client.post('/api/devices/david-001/commands',json={'on':True},headers=headers(csrf)).status_code==409
    assert db.all('SELECT * FROM commands')==[]

@pytest.mark.parametrize('payload',[{}, {'motor':100}, {'brightness':0}, {'brightness':101}, {'brightness':True}, {'on':1}, {'scene':'arbitrary-effect'}, {'status_brightness':21}, {'zone':'penis-status','music':True}, {'zone':'head','scene':'music'}])
def test_strict_commands(setup,payload):
    app,db,client,owner,csrf,*_=setup
    assert client.post('/api/devices/david-001/commands',json=payload,headers=headers(csrf)).status_code==422

def test_device_auth_rejects_wrong_token_query_and_browser_origin(setup):
    app,db,client,*_=setup
    for path,h in [('/ws/devices/david-001',{'Authorization':'Bearer wrong'}),('/ws/devices/david-001?token=bad',{'Authorization':'Bearer '+'a'*48}),('/ws/devices/david-001',{'Authorization':'Bearer '+'a'*48,'Origin':ORIGIN})]:
        with pytest.raises(Exception):
            with client.websocket_connect(ORIGIN.replace("https://","wss://")+path,headers=h): pass

def test_command_roundtrip_ack_reported_and_replay(setup):
    app,db,client,owner,csrf,*_=setup
    with client.websocket_connect('wss://lamp.example.invalid/ws/devices/david-001',headers={'Authorization':'Bearer '+'a'*48}) as ws:
        hello=ws.receive_json(); assert hello['protocol']==1
        ws.send_json(telemetry());assert ws.receive_json()['type']=='heartbeat'
        sent=client.post('/api/devices/david-001/commands',json={'brightness':30},headers=headers(csrf)).json()
        command=ws.receive_json();assert command['session']==hello['session'];assert command['payload']=={'brightness':30}
        assert command['expires']-time.time()<=10
        view=client.get('/api/devices/david-001').json()
        assert view['reported']['brightness']==65 # desired isn't physical evidence
        assert view['desired']=={'brightness':30}
        ws.send_json({'type':'ack','id':sent['id'],'seq':command['seq'],'status':'applied'})
        ws.send_json(telemetry());ws.receive_json()
        assert client.get(f"/api/devices/david-001/commands/{sent['id']}").json()['status']=='applied'
        ws.send_json({'type':'ack','id':sent['id'],'seq':command['seq'],'status':'applied'})
        with pytest.raises(Exception):ws.receive_json()
    assert not client.get('/api/devices/david-001').json()['online']

def test_zone_requires_calibration_and_protects_status(setup):
    app,db,client,owner,csrf,*_=setup
    with client.websocket_connect('wss://lamp.example.invalid/ws/devices/david-001',headers={'Authorization':'Bearer '+'a'*48}) as ws:
        ws.receive_json();ws.send_json(telemetry());ws.receive_json()
        assert client.post('/api/devices/david-001/commands',json={'zone':'head','scene':'blue'},headers=headers(csrf)).status_code==422
        ws.send_json(telemetry(zones_ready=True));ws.receive_json()
        assert client.post('/api/devices/david-001/commands',json={'zone':'penis-status','scene':'blue'},headers=headers(csrf)).status_code==422
        assert client.post('/api/devices/david-001/commands',json={'zone':'head','scene':'blue'},headers=headers(csrf)).status_code==200
        assert ws.receive_json()['payload']['zone']=='head'

def test_guest_invite_curated_expiry_and_revocation(setup):
    app,db,client,owner,csrf,*_=setup
    invitation=client.post('/api/devices/david-001/invites',json={'hours':1},headers=headers(csrf)).json()
    code=invitation['url'].split('#')[1]
    assert db.one('SELECT hash FROM invites')['hash']==digest(code)
    guest=TestClient(app,base_url=ORIGIN)
    assert guest.post('/api/invites/redeem',json={'code':code},headers={'Origin':ORIGIN}).status_code==200
    session=guest.get('/api/session').json()
    assert session['role']=='guest'
    assert guest.post('/api/devices/david-001/commands',json={'status_brightness':5},headers=headers(session['csrf'])).status_code==403
    assert guest.get('/api/devices/david-002').status_code==403
    assert guest.get('/api/devices/david-001/events').status_code==403
    assert guest.post('/api/invites/redeem',json={'code':code},headers={'Origin':ORIGIN}).status_code==403
    assert client.delete('/api/devices/david-001/guests',headers=headers(csrf)).status_code==200
    assert guest.get('/api/session').status_code==401

def test_telemetry_rejects_microphone_payload_and_secrets_absent(setup):
    app,db,client,owner,csrf,*_=setup
    with client.websocket_connect('wss://lamp.example.invalid/ws/devices/david-001',headers={'Authorization':'Bearer '+'a'*48}) as ws:
        ws.receive_json();ws.send_json(telemetry(audio=[1,2,3]))
        with pytest.raises(Exception):ws.receive_json()
    output=client.get('/api/devices/david-001').text+client.get('/api/devices/david-001/events').text
    assert 'a'*48 not in output and 'c'*24 not in output

def test_expired_sessions_and_invites(setup):
    app,db,client,owner,csrf,*_=setup
    expired='e'*32;db.execute('INSERT INTO invites VALUES(?,?,?)',(digest(expired),'david-001',time.time()-1))
    assert client.post('/api/invites/redeem',json={'code':expired},headers={'Origin':ORIGIN}).status_code==403
    db.execute('UPDATE sessions SET expires=?',(time.time()-1,))
    assert client.get('/api/session').status_code==401

def test_production_has_no_demo_and_browser_security_headers(setup):
    app,db,client,*_=setup
    assert client.post('/api/demo/login').status_code==404
    page=client.get('/')
    assert "frame-ancestors 'none'" in page.headers['content-security-policy']
    assert page.headers['referrer-policy']=='no-referrer'
    assert 'microphone=()' in page.headers['permissions-policy']

def test_configuration_fail_closed():
    with pytest.raises(ValueError):Config(demo=True,public_origin='https://public.invalid').validate()
    with pytest.raises(ValueError):Config().validate()

def test_sequences_persist_across_restart(setup):
    app,db,*_=setup
    a=db.command('david-001',{'on':True});b=db.command('david-001',{'on':False})
    assert b['seq']==a['seq']+1

def test_invalid_host_and_oversize_body(setup):
    app,db,client,owner,csrf,*_=setup
    assert client.get('/api/session',headers={'Host':'evil.invalid'}).status_code==400
    assert client.post('/api/devices/david-001/commands',content='x'*4097,headers=headers(csrf)).status_code==413

def test_only_explicit_operator_subject_gets_fleet_authority(setup):
    app,db,client,*_=setup
    app.state.config.admin_subjects=['issuer|operator']
    token,csrf=db.session(subject='issuer|operator',role='admin')
    client.cookies.set('oc_session',token)
    assert len(client.get('/api/devices').json())==2
    assert client.get('/api/devices/david-002').status_code==200
    token,_=db.session(subject='issuer|impostor',role='admin')
    client.cookies.set('oc_session',token)
    assert client.get('/api/devices/david-001').status_code==403
    assert client.get('/api/devices').json()==[]

def test_webp_art_served_without_os_mime_database(tmp_path, monkeypatch):
    import mimetypes
    mimetypes.init()
    monkeypatch.delitem(mimetypes.types_map, '.webp', raising=False)
    monkeypatch.delitem(mimetypes.common_types, '.webp', raising=False)
    app=create_app(Config(database=str(tmp_path/'art.sqlite'), demo=True))
    with TestClient(app, base_url='http://127.0.0.1:8787') as client:
        response=client.get('/assets/david-statue.webp')
    assert response.status_code==200
    assert response.headers['content-type']=='image/webp'
    assert response.content[:4]==b'RIFF' and response.content[8:12]==b'WEBP'


def operator_session(app,db,client):
    app.state.config.admin_subjects=['issuer|operator']
    token,csrf=db.session(subject='issuer|operator',role='admin')
    client.cookies.set('oc_session',token)
    return csrf


def test_admin_fleet_denies_owner_impostor_and_anonymous(setup):
    app,db,client,*_=setup
    assert client.get('/api/admin/devices').status_code==403
    assert client.get('/admin').status_code==403
    token,_=db.session(subject='issuer|impostor',role='admin')
    client.cookies.set('oc_session',token)
    assert client.get('/api/admin/devices').status_code==403
    client.cookies.clear()
    assert client.get('/api/admin/devices').status_code==401
    assert client.get('/admin',follow_redirects=False).status_code==303


def test_admin_fleet_ip_privacy_and_no_credentials(setup):
    app,db,client,*_=setup
    with client.websocket_connect('wss://lamp.example.invalid/ws/devices/david-001',headers={'Authorization':'Bearer '+'a'*48}) as ws:
        ws.receive_json();ws.send_json(telemetry(local_ip='10.10.10.42',free_heap=120000,management_protocol=1));ws.receive_json()
        assert 'local_ip' not in client.get('/api/devices/david-001').json()['reported']
        operator_session(app,db,client)
        rows=client.get('/api/admin/devices').json()
        assert len(rows)==2 and rows[0]['reported']['local_ip']=='10.10.10.42'
        assert rows[0]['claimed'] is True and rows[1]['claimed'] is False
        output=json.dumps(rows)
        for secret in ('credential_hash','claim_hash','issuer|owner','csrf','a'*48,'c'*24):assert secret not in output
        assert client.get('/admin').status_code==200


def test_maintenance_roundtrip_and_no_lighting_desired_corruption(setup):
    app,db,client,*_=setup
    csrf=operator_session(app,db,client)
    with client.websocket_connect('wss://lamp.example.invalid/ws/devices/david-001',headers={'Authorization':'Bearer '+'a'*48}) as ws:
        hello=ws.receive_json();ws.send_json(telemetry(management_protocol=1,body_count=195));ws.receive_json()
        assert client.post('/api/admin/devices/david-001/actions',json={'action':'identify'}).status_code==403
        response=client.post('/api/admin/devices/david-001/actions',json={'action':'locate_pixel','index':194},headers=headers(csrf))
        assert response.status_code==200
        cmd=ws.receive_json();assert cmd['capability']=='maintenance' and cmd['session']==hello['session']
        assert cmd['payload']=={'action':'locate_pixel','index':194} and cmd['expires']-time.time()<=10
        assert db.one('SELECT desired FROM devices WHERE id=?',('david-001',))['desired']=='{}'
        ws.send_json({'type':'ack','id':cmd['id'],'seq':cmd['seq'],'status':'applied'})
        ws.send_json(telemetry(management_protocol=1,body_count=195));ws.receive_json()
        assert client.get('/api/admin/devices').json()[0]['recent_commands'][0]['status']=='applied'
        assert client.post('/api/admin/devices/david-001/actions',json={'action':'locate_pixel','index':195},headers=headers(csrf)).status_code==422
    assert client.post('/api/admin/devices/david-001/actions',json={'action':'reboot'},headers=headers(csrf)).status_code==409


@pytest.mark.parametrize('payload',[{'action':'erase'},{'action':'reboot','index':1},{'action':'locate_pixel'}, {'action':'locate_pixel','index':True}, {'action':'identify','gpio':4}])
def test_maintenance_strict_actions(setup,payload):
    app,db,client,*_=setup
    csrf=operator_session(app,db,client)
    assert client.post('/api/admin/devices/david-001/actions',json=payload,headers=headers(csrf)).status_code==422


def test_maintenance_requires_supported_device_and_separate_lighting_gate(setup):
    app,db,client,*_=setup
    csrf=operator_session(app,db,client)
    with client.websocket_connect('wss://lamp.example.invalid/ws/devices/david-001',headers={'Authorization':'Bearer '+'a'*48}) as ws:
        ws.receive_json();ws.send_json(telemetry());ws.receive_json()
        assert client.post('/api/admin/devices/david-001/actions',json={'action':'reboot'},headers=headers(csrf)).status_code==409
        ws.send_json(telemetry(lighting_ready=False,management_protocol=1));ws.receive_json()
        assert client.post('/api/admin/devices/david-001/actions',json={'action':'identify'},headers=headers(csrf)).status_code==409
        assert client.post('/api/admin/devices/david-001/actions',json={'action':'refresh'},headers=headers(csrf)).status_code==200
        assert ws.receive_json()['payload']=={'action':'refresh'}


def test_admin_ip_validation_rejects_script_input(setup):
    from pydantic import ValidationError
    from server.protocol import Telemetry
    with pytest.raises(ValidationError):Telemetry.model_validate(telemetry(local_ip='javascript:x'))
    with pytest.raises(ValidationError):Telemetry.model_validate(telemetry(audio_level=999))
