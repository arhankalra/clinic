import sqlite3
from pathlib import Path

_conn = None

def init_db(db_path: str):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            nctid TEXT NOT NULL,
            UNIQUE(username, nctid)
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect('app.db', check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn
