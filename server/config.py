import json
import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

@dataclass
class Config:
    database: str = '.local/oddcurrent.sqlite'
    public_origin: str = 'http://127.0.0.1:8787'
    demo: bool = False
    oidc_issuer: str = ''
    oidc_client_id: str = ''
    oidc_client_secret: str = ''
    session_key: str = field(default_factory=lambda: secrets.token_urlsafe(48))

    def validate(self):
        url = urlparse(self.public_origin)
        if url.path or url.query or url.fragment or url.username:
            raise ValueError('public_origin must be an origin only')
        if self.demo:
            if url.hostname not in ('127.0.0.1', 'localhost', '::1'):
                raise ValueError('demo is loopback only')
        elif url.scheme != 'https' or not self.oidc_client_id or urlparse(self.oidc_issuer).scheme != 'https':
            raise ValueError('production requires HTTPS origin and OIDC issuer/client')
        if len(self.session_key) < 32:
            raise ValueError('session key too short')
        return self

    @classmethod
    def load(cls, path):
        p = Path(path)
        if p.stat().st_mode & 0o077:
            raise ValueError('configuration containing credentials must be mode 0600')
        return cls(**json.loads(p.read_text())).validate()
