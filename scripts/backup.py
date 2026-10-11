import argparse
import os
import sqlite3
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
a=p.parse_args()
fd=os.open(a.destination,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
with sqlite3.connect(f'file:{a.source.resolve()}?mode=ro',uri=True) as source, sqlite3.connect(a.destination) as dest:
    source.backup(dest)
    if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise SystemExit('Backup integrity failed')
print('SQLite online backup created with integrity check; independent restore acceptance remains separate.')
