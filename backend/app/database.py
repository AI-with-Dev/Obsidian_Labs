import sqlite3
from contextlib import contextmanager
from typing import Generator
from backend.app.config import settings

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA synchronous = NORMAL;

-- Master receipts table
CREATE TABLE IF NOT EXISTS receipts (
    id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    vendor TEXT,
    receipt_date TEXT,
    currency TEXT NOT NULL DEFAULT 'INR',
    total_paise INTEGER,
    category TEXT,
    status TEXT NOT NULL,
    raw_extraction_json TEXT,
    flags_json TEXT NOT NULL DEFAULT '[]',
    duplicate_of_receipt_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TEXT,
    FOREIGN KEY(duplicate_of_receipt_id) REFERENCES receipts(id) ON DELETE SET NULL
);

-- Receipt line items table
CREATE TABLE IF NOT EXISTS receipt_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id TEXT NOT NULL,
    item_order INTEGER NOT NULL DEFAULT 0,
    description TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 1.0,
    line_total_paise INTEGER NOT NULL,
    FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);

-- Receipt audit event trail
CREATE TABLE IF NOT EXISTS receipt_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    details_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);

-- Indices for performance and duplicate lookup
CREATE INDEX IF NOT EXISTS idx_receipts_file_hash ON receipts(file_hash);
CREATE INDEX IF NOT EXISTS idx_receipts_status ON receipts(status);
CREATE INDEX IF NOT EXISTS idx_receipts_vendor_date ON receipts(vendor, receipt_date);
CREATE INDEX IF NOT EXISTS idx_items_receipt_id ON receipt_items(receipt_id);
"""


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """Return a configured SQLite connection."""
    target_path = str(settings.database_path_resolved if db_path is None else db_path)
    conn = sqlite3.connect(target_path, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def get_db(db_path: str = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite transactions."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = None) -> None:
    """Initialize database tables and indices."""
    with get_db(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
