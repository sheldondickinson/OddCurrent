"""Verify the pinned consumer assets and load order, without an upstream network dependency."""
import hashlib
import json
from pathlib import Path


def test_pinned_313_assets_match_release_lock():
    lock=json.loads(Path('design-system.lock.json').read_text())
    assert lock['version']=='1.1.0' and lock['ref']=='v1.1.0' and lock['autoUpgrade'] is False
    for asset in lock['assets'].values():
        data=Path(asset['path']).read_bytes()
        assert len(data)==asset['bytes']
        assert hashlib.sha256(data).hexdigest()==asset['sha256']


def test_shared_css_precedes_application_adapters():
    for filename in ('web/index.html','web/admin.html'):
        html=Path(filename).read_text()
        assert html.index('/1.1.0/tokens.css')<html.index('/1.1.0/components.css')<html.index('/assets/command-adapter.css')
        assert 'class="c313"' in html
    assert 'c313-button--primary' in Path('web/admin.html').read_text()
