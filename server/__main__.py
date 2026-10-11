import argparse
import uvicorn
from .app import create_app
from .config import Config

parser = argparse.ArgumentParser()
parser.add_argument('--config', help='private 0600 configuration JSON')
parser.add_argument('--demo', action='store_true', help='loopback-only simulator')
parser.add_argument('--port', type=int, default=8787)
args = parser.parse_args()
if args.demo and args.config:
    parser.error('demo and config are mutually exclusive')
config = Config(demo=True, public_origin=f'http://127.0.0.1:{args.port}') if args.demo else Config.load(args.config or '/run/secrets/runtime.json')
uvicorn.run(create_app(config), host='127.0.0.1' if args.demo else '0.0.0.0', port=args.port,
            access_log=False, ws_max_size=4096, ws_ping_interval=15, ws_ping_timeout=20)
