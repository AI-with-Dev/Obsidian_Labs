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
    owner_id INTEGER NOT NULL REFERENCES shop_owner(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    vendor TEXT,
    receipt_date TEXT,
    currency TEXT NOT NULL DEFAULT 'INR',
    total_paise INTEGER,
    category TEXT,
    firm_name TEXT,
    customer_name TEXT,
    transaction_type TEXT NOT NULL DEFAULT 'expense',
    status TEXT NOT NULL,
    raw_extraction_json TEXT,
    flags_json TEXT NOT NULL DEFAULT '[]',
    data TEXT,
    type TEXT NOT NULL DEFAULT 'expense',
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
CREATE INDEX IF NOT EXISTS idx_receipts_type ON receipts(type);
CREATE INDEX IF NOT EXISTS idx_receipts_created_at ON receipts(created_at);
CREATE INDEX IF NOT EXISTS idx_receipts_date ON receipts(receipt_date);
CREATE INDEX IF NOT EXISTS idx_items_receipt_id ON receipt_items(receipt_id);

CREATE TABLE IF NOT EXISTS shop_owner (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    business_name TEXT NOT NULL,
    phone TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    gstin TEXT NOT NULL DEFAULT '',
    language TEXT NOT NULL DEFAULT 'en',
    currency TEXT NOT NULL DEFAULT 'INR',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS login_sessions (
    token_hash TEXT PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES shop_owner(id) ON DELETE CASCADE,
    expires_at INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_login_sessions_expiry ON login_sessions(expires_at);
"""


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """Return a high-concurrency configured SQLite connection capable of 1000s of requests."""
    target_path = str(settings.database_path_resolved if db_path is None else db_path)
    conn = sqlite3.connect(target_path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;")
    conn.execute("PRAGMA mmap_size = 268435456;")
    conn.execute("PRAGMA temp_store = MEMORY;")
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
    """Initialize database tables, indices, and migrations."""
    with get_db(db_path) as conn:
        conn.executescript(SCHEMA_SQL)

        owner_table = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'shop_owner';"
        ).fetchone()
        if owner_table and "CHECK (ID = 1)" in owner_table["sql"].upper():
            conn.execute("PRAGMA foreign_keys = OFF;")
            conn.execute(
                """
                CREATE TABLE shop_owner_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    password_hash TEXT NOT NULL,
                    business_name TEXT NOT NULL,
                    phone TEXT NOT NULL DEFAULT '',
                    address TEXT NOT NULL DEFAULT '',
                    gstin TEXT NOT NULL DEFAULT '',
                    language TEXT NOT NULL DEFAULT 'en',
                    currency TEXT NOT NULL DEFAULT 'INR',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.execute(
                "INSERT INTO shop_owner_new SELECT * FROM shop_owner;"
            )
            conn.execute(
                """
                CREATE TABLE login_sessions_new (
                    token_hash TEXT PRIMARY KEY,
                    owner_id INTEGER NOT NULL REFERENCES shop_owner_new(id) ON DELETE CASCADE,
                    expires_at INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.execute(
                "INSERT INTO login_sessions_new SELECT * FROM login_sessions;"
            )
            conn.execute("DROP TABLE login_sessions;")
            conn.execute("DROP TABLE shop_owner;")
            conn.execute("ALTER TABLE shop_owner_new RENAME TO shop_owner;")
            conn.execute("ALTER TABLE login_sessions_new RENAME TO login_sessions;")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_login_sessions_expiry ON login_sessions(expires_at);"
            )
            conn.commit()
            conn.execute("PRAGMA foreign_keys = ON;")

        # Idempotent migrations for new receipt fields
        receipt_cols = {row[1] for row in conn.execute("PRAGMA table_info(receipts);").fetchall()}
        if "owner_id" not in receipt_cols:
            conn.execute(
                "ALTER TABLE receipts ADD COLUMN owner_id INTEGER REFERENCES shop_owner(id) ON DELETE CASCADE;"
            )
            conn.execute(
                "UPDATE receipts SET owner_id = (SELECT MIN(id) FROM shop_owner) WHERE owner_id IS NULL;"
            )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_receipts_owner_id ON receipts(owner_id);"
        )
        if "invoice_number" not in receipt_cols:
            conn.execute("ALTER TABLE receipts ADD COLUMN invoice_number TEXT;")
        if "tax_paise" not in receipt_cols:
            conn.execute("ALTER TABLE receipts ADD COLUMN tax_paise INTEGER;")
        if "discount_paise" not in receipt_cols:
            conn.execute("ALTER TABLE receipts ADD COLUMN discount_paise INTEGER;")
        if "payment_method" not in receipt_cols:
            conn.execute("ALTER TABLE receipts ADD COLUMN payment_method TEXT;")
        if "notes" not in receipt_cols:
            conn.execute("ALTER TABLE receipts ADD COLUMN notes TEXT;")
        if "data" not in receipt_cols:
            conn.execute("ALTER TABLE receipts ADD COLUMN data TEXT;")
        if "type" not in receipt_cols:
            conn.execute("ALTER TABLE receipts ADD COLUMN type TEXT DEFAULT 'expense';")
        if "firm_name" not in receipt_cols:
            conn.execute("ALTER TABLE receipts ADD COLUMN firm_name TEXT;")
        if "customer_name" not in receipt_cols:
            conn.execute("ALTER TABLE receipts ADD COLUMN customer_name TEXT;")
        if "transaction_type" not in receipt_cols:
            conn.execute("ALTER TABLE receipts ADD COLUMN transaction_type TEXT NOT NULL DEFAULT 'expense';")

        item_cols = {row[1] for row in conn.execute("PRAGMA table_info(receipt_items);").fetchall()}
        if "unit_price_paise" not in item_cols:
            conn.execute("ALTER TABLE receipt_items ADD COLUMN unit_price_paise INTEGER;")
