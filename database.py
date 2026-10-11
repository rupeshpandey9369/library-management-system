import sqlite3
from pathlib import Path
 
# library.db will sit next to this file, no matter where you run the app from
DB_PATH = Path(__file__).parent / "library.db"
 
 
def get_connection():
    """Open a connection to library.db (the file is auto-created if missing)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # rows behave like dicts: row["title"]
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite ignores FKs unless we ask
    return conn
 
 
def init_db():
    """Create the 3 tables on first run. Safe to call every time."""
    conn = get_connection()
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            book_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title            TEXT NOT NULL,
            author           TEXT NOT NULL,
            isbn             TEXT,
            category         TEXT,
            description      TEXT,
            total_copies     INTEGER NOT NULL CHECK (total_copies >= 0),
            available_copies INTEGER NOT NULL CHECK (available_copies >= 0)
        );
 
        CREATE TABLE IF NOT EXISTS members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            email     TEXT NOT NULL UNIQUE,
            phone     TEXT,
            joined_on TEXT NOT NULL
        );
 
        CREATE TABLE IF NOT EXISTS loans (
            loan_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id   INTEGER NOT NULL,
            book_id     INTEGER NOT NULL,
            issue_date  TEXT NOT NULL,
            due_date    TEXT NOT NULL,
            return_date TEXT,
            fine_amount INTEGER NOT NULL DEFAULT 0,
            status      TEXT NOT NULL DEFAULT 'issued'
                        CHECK (status IN ('issued', 'returned')),
            FOREIGN KEY (member_id) REFERENCES members(member_id),
            FOREIGN KEY (book_id)   REFERENCES books(book_id)
        );
        """)
        conn.commit()
    finally:
        conn.close()
 
 
def fetch_all(query, params=()):
    """Run a SELECT and return a list of dicts."""
    conn = get_connection()
    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
 
 
def fetch_one(query, params=()):
    """Run a SELECT and return one dict (or None)."""
    conn = get_connection()
    try:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
 
 
def execute(query, params=()):
    """Run INSERT / UPDATE / DELETE. Returns the new row id (for INSERT)."""
    conn = get_connection()
    try:
        cur = conn.execute(query, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()
 
 
if __name__ == "__main__":
    init_db()
    print("Database ready at:", DB_PATH)
 