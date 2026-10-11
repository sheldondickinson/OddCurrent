"""Unique identities, AP QR and private claim inserts; never prints secret values."""
import argparse
import json
import os
import re
import secrets
from pathlib import Path
from urllib.parse import urlparse
import qrcode
import qrcode.image.svg

def private_write(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f: f.write(text)

def wifi_escape(text):
    return re.sub(r'([\\;,:\"])', r'\\\1', text)

def create(serial, origin, broker_host, ca_pem, out):
    if not (re.fullmatch(r'[a-z0-9][a-z0-9-]{3,31}', serial)): raise ValueError('DNS-safe unique serial required')
    url = urlparse(origin)
    if not (url.scheme == 'https' and url.hostname and not (url.username or url.query or url.fragment)): raise ValueError('HTTPS public origin required')
    if not (re.fullmatch(r'[a-zA-Z0-9.-]+', broker_host)): raise ValueError('broker hostname required')
    if not ('BEGIN CERTIFICATE' in ca_pem and 'PRIVATE KEY' not in ca_pem): raise ValueError('public CA certificate required')
    out = Path(out)
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(out, 0o700)
    identity = {'schema_version': '1.0.0', 'serial': serial, 'profile': 'david-v1',
                'mdns': serial, 'public_url': origin.rstrip('/') + '/d/' + serial,
                'ap_ssid': 'ODDCURRENT-SETUP-' + serial[-8:], 'ap_password': secrets.token_urlsafe(18),
                'device_credential': secrets.token_urlsafe(32), 'claim_code': secrets.token_urlsafe(24),
                'broker_host': broker_host, 'broker_port': 443, 'ca_pem': ca_pem}
    private_write(out / 'factory.json', json.dumps(identity, indent=2) + '\n')
    private_write(out / 'claim-insert.txt', f"Private ownership code for {serial}\n{identity['claim_code']}\nKeep inside the base. NFC alone does not claim ownership.\n")
    payload = f"WIFI:T:WPA;S:{wifi_escape(identity['ap_ssid'])};P:{wifi_escape(identity['ap_password'])};;"
    image = qrcode.make(payload, image_factory=qrcode.image.svg.SvgPathImage, border=4)
    with open(out / 'setup-qr.svg', 'xb') as f: image.save(f)
    os.chmod(out / 'setup-qr.svg', 0o600)
    private_write(out / 'base-label.txt', f"{serial} · OddCurrent / David\nScan the setup QR, then open http://4.3.2.1 if setup does not appear.\nHold recessed setup 5 seconds to change Wi-Fi; 15 seconds clears home Wi-Fi only.\n")
    private_write(out / 'nfc-url.txt', identity['public_url'] + '\n')
    return identity

def main():
    p = argparse.ArgumentParser()
    p.add_argument('serial'); p.add_argument('--origin', required=True)
    p.add_argument('--broker-host', required=True); p.add_argument('--ca', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    create(a.serial, a.origin, a.broker_host, a.ca.read_text(), a.out)
    print('Private factory bundle created. No device flashed or HTTPS route verified.')

if __name__ == '__main__': main()
