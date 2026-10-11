"""Import a private factory bundle into the central DB. No plaintext central secret."""
import argparse
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server.store import Store

parser = argparse.ArgumentParser()
parser.add_argument('--factory', type=Path, required=True)
parser.add_argument('--database', required=True)
a = parser.parse_args()
if a.factory.stat().st_mode & 0o077: raise SystemExit('factory file must be mode 0600')
identity = json.loads(a.factory.read_text())
if not re.fullmatch(r'[a-z0-9][a-z0-9-]{3,31}', identity['serial']): raise SystemExit('invalid serial')
if identity['profile'] != 'david-v1': raise SystemExit('profile not supported by factory importer')
Store(a.database).register(identity['serial'], identity['profile'], identity['device_credential'], identity['claim_code'])
print('Registered unique device with hashed credential and one-time claim code.')
