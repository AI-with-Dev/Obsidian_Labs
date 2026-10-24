import argparse
import sqlite3
from pathlib import Path

from backend.app.config import settings
from backend.app.database import get_db, init_db
from backend.app.services.receipt_service import sanitize_filename
from backend.app.storage import (
    ensure_storage_bucket,
    upload_object,
    validate_storage_configuration,
)


OWNER_COLUMNS = (
    "id, full_name, email, password_hash, business_name, phone, address, gstin, "
    "language, currency, created_at"
)
RECEIPT_COLUMNS = (
    "id, owner_id, file_path, file_name, file_hash, mime_type, vendor, receipt_date, "
    "currency, total_paise, category, firm_name, customer_name, transaction_type, status, "
    "raw_extraction_json, flags_json, data, type, duplicate_of_receipt_id, created_at, updated_at, "
    "confirmed_at, invoice_number, tax_paise, discount_paise, payment_method, notes"
)
ITEM_COLUMNS = (
    "id, receipt_id, item_order, description, quantity, line_total_paise, unit_price_paise"
)
EVENT_COLUMNS = "id, receipt_id, event_type, details_json, created_at"


def _read_rows(connection: sqlite3.Connection, table: str) -> list[dict]:
    return [dict(row) for row in connection.execute(f"SELECT * FROM {table}").fetchall()]


def migrate(sqlite_path: Path, uploads_path: Path) -> None:
    validate_storage_configuration()
    if not settings.uses_supabase_database or not settings.uses_supabase_storage:
        raise RuntimeError(
            "Set DATABASE_URL, SUPABASE_URL, and SUPABASE_SERVICE_ROLE_KEY before migrating."
        )
    if not sqlite_path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {sqlite_path}")

    init_db(str(sqlite_path))
    ensure_storage_bucket()
    init_db()

    source = sqlite3.connect(str(sqlite_path))
    source.row_factory = sqlite3.Row
    try:
        owners = _read_rows(source, "shop_owner")
        receipts = _read_rows(source, "receipts")
        items = _read_rows(source, "receipt_items")
        events = _read_rows(source, "receipt_events")
    finally:
        source.close()

    if not owners:
        raise RuntimeError("The SQLite database contains no accounts to migrate.")

    duplicate_links = [
        (receipt["duplicate_of_receipt_id"], receipt["id"])
        for receipt in receipts
        if receipt["duplicate_of_receipt_id"] is not None
    ]

    with get_db() as destination:
        existing = destination.execute(
            "SELECT (SELECT COUNT(*) FROM shop_owner) AS owners, "
            "(SELECT COUNT(*) FROM receipts) AS receipts"
        ).fetchone()
        if existing["owners"] or existing["receipts"]:
            raise RuntimeError(
                "The Supabase database is not empty; refusing to merge potentially duplicate data."
            )

    for receipt in receipts:
        source_path = Path(receipt["file_path"])
        if not source_path.is_file():
            source_path = uploads_path / source_path.name
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Missing uploaded file for receipt {receipt['id']}: {source_path}"
            )
        object_key = (
            f"{receipt['owner_id']}/"
            f"{receipt['id']}_{sanitize_filename(receipt['file_name'])}"
        )
        upload_object(
            object_key,
            source_path.read_bytes(),
            receipt["mime_type"],
            upsert=True,
        )
        receipt["file_path"] = object_key

    with get_db() as destination:
        for owner in owners:
            values = [owner[column] for column in OWNER_COLUMNS.split(", ")]
            destination.execute(
                f"INSERT INTO shop_owner ({OWNER_COLUMNS}) VALUES "
                f"({', '.join('?' for _ in values)})",
                values,
            )

        receipt_columns = RECEIPT_COLUMNS.split(", ")
        for receipt in receipts:
            receipt["duplicate_of_receipt_id"] = None
            values = [receipt.get(column) for column in receipt_columns]
            destination.execute(
                f"INSERT INTO receipts ({RECEIPT_COLUMNS}) VALUES "
                f"({', '.join('?' for _ in values)})",
                values,
            )

        item_columns = ITEM_COLUMNS.split(", ")
        for item in items:
            values = [item.get(column) for column in item_columns]
            destination.execute(
                f"INSERT INTO receipt_items ({ITEM_COLUMNS}) VALUES "
                f"({', '.join('?' for _ in values)})",
                values,
            )

        event_columns = EVENT_COLUMNS.split(", ")
        for event in events:
            values = [event.get(column) for column in event_columns]
            destination.execute(
                f"INSERT INTO receipt_events ({EVENT_COLUMNS}) VALUES "
                f"({', '.join('?' for _ in values)})",
                values,
            )

        for duplicate_id, receipt_id in duplicate_links:
            destination.execute(
                "UPDATE receipts SET duplicate_of_receipt_id = ? WHERE id = ?",
                (duplicate_id, receipt_id),
            )

        for table in ("shop_owner", "receipt_items", "receipt_events"):
            destination.execute(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', 'id'),
                    COALESCE(MAX(id), 1),
                    COUNT(*) > 0
                )
                FROM {table}
                """
            )

    print(
        f"Migrated {len(owners)} account(s), {len(receipts)} receipt(s), "
        f"{len(items)} line item(s), and {len(events)} audit event(s)."
    )
    print("Login sessions were not migrated; sign in again on each device.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy a local Vyapar Mitra SQLite database and receipt files to Supabase."
    )
    parser.add_argument("--sqlite-path", type=Path, required=True)
    parser.add_argument(
        "--uploads-path",
        type=Path,
        default=Path("backend/data/uploads"),
    )
    args = parser.parse_args()
    migrate(args.sqlite_path, args.uploads_path)


if __name__ == "__main__":
    main()
