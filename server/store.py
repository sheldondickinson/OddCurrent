"""Small single-worker durable store. Credentials and invitations are hash-only."""
import hashlib
import json
import secrets
import sqlite3
import threading
import time
from pathlib import Path

def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

class Store:
    def __init__(self, path: str):
        if path != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.db.executescript('''
          PRAGMA foreign_keys=ON;
          PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY, profile TEXT NOT NULL, credential_hash TEXT NOT NULL,
            claim_hash TEXT, owner TEXT, seq INTEGER NOT NULL DEFAULT 0,
            last_seen REAL, reported TEXT NOT NULL DEFAULT '{}', desired TEXT NOT NULL DEFAULT '{}');
          CREATE TABLE IF NOT EXISTS sessions (
            hash TEXT PRIMARY KEY, subject TEXT, device TEXT, role TEXT NOT NULL,
            csrf TEXT NOT NULL, expires REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS invites (
            hash TEXT PRIMARY KEY, device TEXT NOT NULL, expires REAL NOT NULL,
            FOREIGN KEY(device) REFERENCES devices(id));
          CREATE TABLE IF NOT EXISTS commands (
            id TEXT PRIMARY KEY, device TEXT NOT NULL, seq INTEGER NOT NULL,
            expires REAL NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY, device TEXT NOT NULL, at REAL NOT NULL, kind TEXT NOT NULL);
        ''')
        if path != ':memory:':
            Path(path).chmod(0o600)

    def one(self, sql, params=()):
        with self.lock:
            row = self.db.execute(sql, params).fetchone()
            return dict(row) if row else None

    def all(self, sql, params=()):
        with self.lock:
            return [dict(x) for x in self.db.execute(sql, params).fetchall()]

    def execute(self, sql, params=()):
        with self.lock:
            return self.db.execute(sql, params)

    def register(self, device_id, profile, credential, claim):
        self.execute('INSERT INTO devices(id,profile,credential_hash,claim_hash) VALUES(?,?,?,?)',
                     (device_id, profile, digest(credential), digest(claim)))

    def session(self, subject=None, device=None, role='owner', hours=12):
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        self.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?)',
                     (digest(token), subject, device, role, csrf, time.time() + hours * 3600))
        return token, csrf

    def claim(self, device, code, subject):
        with self.lock:
            result = self.db.execute('UPDATE devices SET owner=?,claim_hash=NULL WHERE id=? AND owner IS NULL AND claim_hash=?',
                                     (subject, device, digest(code)))
            return result.rowcount == 1

    def event(self, device, kind):
        # Callers use fixed event names, never user-provided messages.
        self.execute('INSERT INTO events(device,at,kind) VALUES(?,?,?)', (device, time.time(), kind))
        self.execute('DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT 1000)')

    def command(self, device, payload, capability='lighting'):
        if capability not in ('lighting', 'maintenance'):
            raise ValueError('unsupported command capability')
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                if capability == 'lighting':
                    seq = self.db.execute('UPDATE devices SET seq=seq+1,desired=? WHERE id=? RETURNING seq',
                                          (json.dumps(payload), device)).fetchone()[0]
                else:
                    seq = self.db.execute('UPDATE devices SET seq=seq+1 WHERE id=? RETURNING seq', (device,)).fetchone()[0]
                cmd = {'type': 'command', 'id': secrets.token_hex(16), 'seq': seq,
                       'expires': int(time.time()) + 10, 'capability': capability, 'payload': payload}
                self.db.execute('INSERT INTO commands VALUES(?,?,?,?,?,?)',
                                (cmd['id'], device, seq, cmd['expires'], 'pending', json.dumps(payload)))
                self.db.execute('DELETE FROM commands WHERE expires < ?', (time.time() - 86400,))
                self.db.execute('COMMIT')
                return cmd
            except Exception:
                self.db.execute('ROLLBACK')
                raise
