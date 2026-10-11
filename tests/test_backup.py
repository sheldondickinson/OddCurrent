import sqlite3
import subprocess
import sys
from server.store import Store

def test_backup_restores_identity_owner_and_sequence(tmp_path):
    source=tmp_path/'source.sqlite';backup=tmp_path/'backup.sqlite'
    store=Store(str(source));store.register('test-lamp-001','david-v1','credential-fixture','claim-fixture')
    store.claim('test-lamp-001','claim-fixture','issuer|owner');store.command('test-lamp-001',{'on':True})
    subprocess.run([sys.executable,'scripts/backup.py',str(source),str(backup)],check=True)
    restored=Store(str(backup))
    assert restored.one('SELECT owner,seq FROM devices')=={'owner':'issuer|owner','seq':1}
    assert restored.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
