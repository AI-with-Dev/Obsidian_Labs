import hashlib
import json
import re
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional, Tuple
from fastapi import HTTPException, UploadFile, status

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import ReceiptUpdatePayload

ALLOWED_MIMES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and shell injection."""
    base = Path(filename).name
    # Keep only alphanumeric, dots, underscores, dashes
    clean = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return clean or "receipt_upload"


def normalize_vendor_name(vendor: Optional[str]) -> str:
    """Normalize vendor name for duplicate comparison: lowercase alphanumeric only."""
    if not vendor:
        return ""
    return re.sub(r"[^a-z0-9]", "", vendor.lower())


def find_similar_confirmed_duplicate(
    vendor: str,
    receipt_date: str,
    total_paise: Optional[int],
    exclude_id: str,
) -> Optional[dict]:
    """Check if normalized vendor + receipt_date + total_paise matches an existing confirmed receipt."""
    if not vendor or not receipt_date or total_paise is None or total_paise <= 0:
        return None

    norm_target = normalize_vendor_name(vendor)
    if not norm_target:
        return None

    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, vendor, receipt_date, total_paise
            FROM receipts
            WHERE status = 'confirmed' AND receipt_date = ? AND total_paise = ? AND id != ?;
            """,
            (receipt_date, total_paise, exclude_id),
        ).fetchall()

        for r in rows:
            if normalize_vendor_name(r["vendor"]) == norm_target:
                return dict(r)

    return None


async def process_and_save_upload(file: UploadFile) -> str:
    """Validate, hash, store upload, check SHA-256 duplicates, and record in database."""
    raw_filename = file.filename or "receipt.jpg"
    safe_name = sanitize_filename(raw_filename)
    ext = Path(safe_name).suffix.lower()

    content_type = (file.content_type or "").lower()

    # Determine & validate MIME / extension
    if ext not in ALLOWED_EXTENSIONS and content_type not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Please upload a JPG, PNG, or PDF file.",
        )

    # Normalize content type if missing or generic
    if content_type not in ALLOWED_MIMES:
        if ext in {".jpg", ".jpeg"}:
            content_type = "image/jpeg"
        elif ext == ".png":
            content_type = "image/png"
        elif ext == ".pdf":
            content_type = "application/pdf"

    # Read content with size guard
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty. Please choose a valid receipt file.",
        )

    if len(content) > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size ({settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB).",
        )

    # Compute SHA-256
    file_hash = hashlib.sha256(content).hexdigest()

    # Generate unique receipt ID
    receipt_id = f"rec_{uuid.uuid4().hex[:12]}"

    # Save to disk
    stored_filename = f"{receipt_id}_{safe_name}"
    target_path = settings.upload_dir_resolved / stored_filename
    target_path.write_bytes(content)

    # Check for exact duplicate by SHA-256 hash
    duplicate_of_id = None
    initial_status = "uploaded"
    initial_flags = []

    with get_db() as conn:
        existing = conn.execute(
            """
            SELECT id FROM receipts
            WHERE file_hash = ? AND status != 'discarded_duplicate'
            ORDER BY created_at ASC LIMIT 1;
            """,
            (file_hash,),
        ).fetchone()

        if existing:
            duplicate_of_id = existing["id"]
            initial_status = "duplicate"
            initial_flags = ["duplicate"]

        # Database insertion
        conn.execute(
            """
            INSERT INTO receipts (
                id, file_path, file_name, file_hash, mime_type,
                currency, status, flags_json, duplicate_of_receipt_id
            ) VALUES (?, ?, ?, ?, ?, 'INR', ?, ?, ?);
            """,
            (
                receipt_id,
                str(target_path),
                safe_name,
                file_hash,
                content_type,
                initial_status,
                json.dumps(initial_flags),
                duplicate_of_id,
            ),
        )

        conn.execute(
            """
            INSERT INTO receipt_events (
                receipt_id, event_type, details_json
            ) VALUES (?, 'UPLOADED', ?);
            """,
            (
                receipt_id,
                json.dumps({
                    "file_name": safe_name,
                    "file_size": len(content),
                    "file_hash": file_hash,
                    "mime_type": content_type,
                    "is_duplicate": bool(duplicate_of_id),
                    "duplicate_of_id": duplicate_of_id,
                }),
            ),
        )

    return receipt_id


def get_receipt_file(receipt_id: str) -> Tuple[Path, str, str]:
    """Retrieve file path, mime type, and filename for an existing receipt."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT file_path, mime_type, file_name FROM receipts WHERE id = ?;",
            (receipt_id,),
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receipt with ID '{receipt_id}' not found.",
            )

        file_path = Path(row["file_path"])
        if not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt file not found on disk.",
            )

        return file_path, row["mime_type"], row["file_name"]


def get_receipt_details(receipt_id: str) -> dict:
    """Retrieve receipt details and line items formatted for the frontend."""
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT id, file_path, file_name, vendor, receipt_date, currency,
                   total_paise, category, status, flags_json, duplicate_of_receipt_id,
                   invoice_number, tax_paise, discount_paise, payment_method, notes
            FROM receipts
            WHERE id = ?;
            """,
            (receipt_id,),
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receipt with ID '{receipt_id}' not found.",
            )

        items_cursor = conn.execute(
            """
            SELECT description, line_total_paise, quantity, unit_price_paise
            FROM receipt_items
            WHERE receipt_id = ?
            ORDER BY item_order ASC, id ASC;
            """,
            (receipt_id,),
        )
        items = []
        subtotal_paise = 0
        for it in items_cursor.fetchall():
            amt = it["line_total_paise"] / 100.0
            subtotal_paise += it["line_total_paise"]
            q = float(it["quantity"]) if it["quantity"] is not None else 1.0
            up = (it["unit_price_paise"] / 100.0) if it["unit_price_paise"] is not None else amt
            items.append({
                "name": it["description"],
                "amount": amt,
                "quantity": q,
                "unitPrice": up,
            })

        flags = json.loads(row["flags_json"] or "[]")
        db_status = row["status"]
        # Map backend database status to frontend contract: 'draft' | 'confirmed' | 'duplicate'
        if db_status == "confirmed":
            frontend_status = "confirmed"
        elif db_status == "duplicate":
            frontend_status = "duplicate"
        else:
            frontend_status = "draft"

        total_val = row["total_paise"] / 100.0 if row["total_paise"] is not None else None
        subtotal_val = subtotal_paise / 100.0 if items else None
        tax_val = (row["tax_paise"] / 100.0) if row["tax_paise"] is not None else None
        discount_val = (row["discount_paise"] / 100.0) if row["discount_paise"] is not None else None

        return {
            "id": row["id"],
            "vendor": row["vendor"] or "",
            "date": row["receipt_date"] or "",
            "currency": row["currency"] or "INR",
            "items": items,
            "total": total_val,
            "category": row["category"] or "other",
            "status": frontend_status,
            "fileUrl": f"/api/receipts/{row['id']}/file",
            "fileName": row["file_name"],
            "flags": flags,
            "duplicateOfId": row["duplicate_of_receipt_id"],
            "invoiceNumber": row["invoice_number"],
            "subtotal": subtotal_val,
            "tax": tax_val,
            "discount": discount_val,
            "paymentMethod": row["payment_method"],
            "notes": row["notes"],
        }


from decimal import Decimal
from backend.app.services.gemini_service import extract_receipt_with_gemini


async def perform_receipt_extraction(receipt_id: str) -> dict:
    """Run structured Gemini extraction on receipt file, check duplicates, save to DB, and return Receipt shape."""
    file_path, mime_type, _ = get_receipt_file(receipt_id)

    # Mark as extracting
    with get_db() as conn:
        conn.execute("UPDATE receipts SET status = 'extracting' WHERE id = ?;", (receipt_id,))

    try:
        extraction, raw_json = extract_receipt_with_gemini(file_path, mime_type)
    except Exception as e:
        with get_db() as conn:
            conn.execute("UPDATE receipts SET status = 'extraction_failed' WHERE id = ?;", (receipt_id,))
            conn.execute(
                "INSERT INTO receipt_events (receipt_id, event_type, details_json) VALUES (?, 'EXTRACTION_FAILED', ?);",
                (receipt_id, json.dumps({"error": str(e)})),
            )
        raise

    # Convert total to integer paise
    total_paise: Optional[int] = None
    if extraction.total is not None:
        try:
            total_paise = int(round(Decimal(str(extraction.total)) * 100))
        except Exception:
            total_paise = None

    with get_db() as conn:
        # Check if already flagged as duplicate by exact SHA-256 upload
        curr = conn.execute(
            "SELECT duplicate_of_receipt_id, status FROM receipts WHERE id = ?;",
            (receipt_id,),
        ).fetchone()

        duplicate_of_id = curr["duplicate_of_receipt_id"] if curr else None
        new_status = "needs_review"
        flags = list(extraction.uncertainty_flags)

        if duplicate_of_id:
            new_status = "duplicate"
            if "duplicate" not in flags:
                flags.append("duplicate")
        else:
            # Check for similar duplicate against confirmed receipts
            similar = find_similar_confirmed_duplicate(
                vendor=extraction.vendor or "",
                receipt_date=extraction.date or "",
                total_paise=total_paise,
                exclude_id=receipt_id,
            )
            if similar:
                duplicate_of_id = similar["id"]
                new_status = "duplicate"
                if "duplicate" not in flags:
                    flags.append("duplicate")

        # Clear any prior extracted items for idempotency/retry
        conn.execute("DELETE FROM receipt_items WHERE receipt_id = ?;", (receipt_id,))

        # Insert extracted line items
        for idx, item in enumerate(extraction.items):
            try:
                line_paise = int(round(Decimal(str(item.amount)) * 100))
            except Exception:
                line_paise = 0

            conn.execute(
                """
                INSERT INTO receipt_items (receipt_id, item_order, description, quantity, line_total_paise, unit_price_paise)
                VALUES (?, ?, ?, 1.0, ?, ?);
                """,
                (receipt_id, idx, item.name or "Item", line_paise, line_paise),
            )

        # Update receipt record
        conn.execute(
            """
            UPDATE receipts
            SET vendor = ?,
                receipt_date = ?,
                currency = ?,
                total_paise = ?,
                category = ?,
                status = ?,
                duplicate_of_receipt_id = ?,
                raw_extraction_json = ?,
                flags_json = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (
                extraction.vendor or "",
                extraction.date or "",
                extraction.currency or "INR",
                total_paise,
                extraction.suggested_category or "other",
                new_status,
                duplicate_of_id,
                raw_json,
                json.dumps(flags),
                receipt_id,
            ),
        )

        conn.execute(
            """
            INSERT INTO receipt_events (receipt_id, event_type, details_json)
            VALUES (?, 'EXTRACTION_COMPLETED', ?);
            """,
            (
                receipt_id,
                json.dumps({
                    "vendor": extraction.vendor,
                    "total": extraction.total,
                    "category": extraction.suggested_category,
                    "items_count": len(extraction.items),
                    "status": new_status,
                    "duplicate_of_id": duplicate_of_id,
                    "flags": flags,
                }),
            ),
        )

    return get_receipt_details(receipt_id)


def list_receipts(
    q: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    category: Optional[str] = None,
    vendor: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> list:
    """List receipts matching search and filter parameters."""
    query = "SELECT id FROM receipts WHERE status != 'discarded_duplicate'"
    params = []

    if status_filter == "confirmed":
        query += " AND status = 'confirmed'"
    elif status_filter == "pending":
        query += " AND status != 'confirmed'"

    if category:
        query += " AND category = ?"
        params.append(category)

    if vendor:
        query += " AND vendor = ?"
        params.append(vendor)

    if from_date:
        query += " AND receipt_date >= ?"
        params.append(from_date)

    if to_date:
        query += " AND receipt_date <= ?"
        params.append(to_date)

    query += " ORDER BY receipt_date DESC, created_at DESC;"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        results = [get_receipt_details(r["id"]) for r in rows]

        if q and q.strip():
            term = q.strip().lower()
            filtered = []
            for item in results:
                vendor_match = term in (item["vendor"] or "").lower()
                items_match = any(term in (it["name"] or "").lower() for it in item["items"])
                if vendor_match or items_match:
                    filtered.append(item)
            return filtered

        return results

ALLOWED_CONFIRM_CATEGORIES = {
    "inventory",
    "packaging",
    "transport",
    "utilities",
    "rent",
    "repairs",
    "other",
}


def save_receipt_draft(receipt_id: str, payload: ReceiptUpdatePayload) -> dict:
    """Save owner corrections and draft edits for an existing receipt."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, status, flags_json FROM receipts WHERE id = ?;",
            (receipt_id,),
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receipt with ID '{receipt_id}' not found.",
            )

        if row["status"] == "discarded_duplicate":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit a discarded duplicate receipt.",
            )

        # Money conversion to integer paise
        total_paise = None
        if payload.total is not None:
            try:
                total_paise = int(round(Decimal(str(payload.total)) * 100))
            except Exception:
                total_paise = None

        # Clean/normalize values
        vendor = (payload.vendor or "").strip()
        date = (payload.date or "").strip()
        currency = (payload.currency or "INR").strip().upper()
        category = (payload.category or "").strip().lower() if payload.category is not None else (row["category"] or "other")
        if category and category not in ALLOWED_CONFIRM_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category '{payload.category}'. Category must be one of: {', '.join(sorted(ALLOWED_CONFIRM_CATEGORIES))}.",
            )

        # Update uncertainty flags: clear flags if user provided valid fields
        existing_flags = set(json.loads(row["flags_json"] or "[]"))
        if vendor:
            existing_flags.discard("vendor")
        if date and re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            existing_flags.discard("date")
        if total_paise is not None and total_paise > 0:
            existing_flags.discard("total")

        # Extract new optional fields
        invoice_number = payload.invoiceNumber.strip() if payload.invoiceNumber is not None else None
        payment_method = payload.paymentMethod.strip() if payload.paymentMethod is not None else None
        notes = payload.notes.strip() if payload.notes is not None else None

        tax_paise = None
        if payload.tax is not None:
            try:
                tax_paise = int(round(Decimal(str(payload.tax)) * 100))
            except Exception:
                tax_paise = None

        discount_paise = None
        if payload.discount is not None:
            try:
                discount_paise = int(round(Decimal(str(payload.discount)) * 100))
            except Exception:
                discount_paise = None

        # Update receipt record
        conn.execute(
            """
            UPDATE receipts
            SET vendor = ?,
                receipt_date = ?,
                currency = ?,
                total_paise = ?,
                category = ?,
                invoice_number = COALESCE(?, invoice_number),
                tax_paise = COALESCE(?, tax_paise),
                discount_paise = COALESCE(?, discount_paise),
                payment_method = COALESCE(?, payment_method),
                notes = COALESCE(?, notes),
                flags_json = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (
                vendor,
                date,
                currency,
                total_paise,
                category,
                invoice_number,
                tax_paise,
                discount_paise,
                payment_method,
                notes,
                json.dumps(list(existing_flags)),
                receipt_id,
            ),
        )

        # Replace items if items list was provided
        if payload.items is not None:
            conn.execute("DELETE FROM receipt_items WHERE receipt_id = ?;", (receipt_id,))
            for idx, item in enumerate(payload.items):
                try:
                    line_paise = int(round(Decimal(str(item.amount)) * 100))
                except Exception:
                    line_paise = 0
                q = float(item.quantity) if item.quantity is not None else 1.0
                try:
                    up_paise = int(round(Decimal(str(item.unitPrice)) * 100)) if item.unitPrice is not None else line_paise
                except Exception:
                    up_paise = line_paise

                conn.execute(
                    """
                    INSERT INTO receipt_items (receipt_id, item_order, description, quantity, line_total_paise, unit_price_paise)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (receipt_id, idx, item.name.strip() or "Item", q, line_paise, up_paise),
                )

        # Audit log event
        conn.execute(
            """
            INSERT INTO receipt_events (receipt_id, event_type, details_json)
            VALUES (?, 'EDITED', ?);
            """,
            (
                receipt_id,
                json.dumps({
                    "vendor": vendor,
                    "date": date,
                    "currency": currency,
                    "total": payload.total,
                    "category": category,
                    "invoice_number": invoice_number,
                    "items_count": len(payload.items) if payload.items is not None else None,
                }),
            ),
        )

    return get_receipt_details(receipt_id)


def confirm_receipt(receipt_id: str) -> dict:
    """Validate and explicitly confirm receipt into the trusted ledger."""
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT id, vendor, receipt_date, currency, total_paise, category, status
            FROM receipts
            WHERE id = ?;
            """,
            (receipt_id,),
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receipt with ID '{receipt_id}' not found.",
            )

        if row["status"] == "discarded_duplicate":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot confirm a discarded duplicate receipt.",
            )

        if row["status"] == "confirmed":
            # Already confirmed, idempotent return
            return get_receipt_details(receipt_id)

        # Strict validations: nonempty vendor, valid ISO date, currency INR, positive total, allowed category
        errors = []

        vendor = (row["vendor"] or "").strip()
        if not vendor:
            errors.append("Vendor name is required.")

        receipt_date = (row["receipt_date"] or "").strip()
        if not receipt_date:
            errors.append("Receipt date is required.")
        else:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", receipt_date):
                errors.append("Receipt date must be in YYYY-MM-DD format.")
            else:
                try:
                    datetime.strptime(receipt_date, "%Y-%m-%d")
                except ValueError:
                    errors.append("Receipt date is not a valid calendar date.")

        currency = (row["currency"] or "").strip().upper()
        if currency != "INR":
            errors.append("Currency must be INR.")

        total_paise = row["total_paise"]
        if total_paise is None or total_paise <= 0:
            errors.append("Receipt total must be a positive amount.")

        category = (row["category"] or "").strip().lower()
        if category not in ALLOWED_CONFIRM_CATEGORIES:
            errors.append(f"Category must be one of: {', '.join(sorted(ALLOWED_CONFIRM_CATEGORIES))}.")

        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot confirm receipt: " + " ".join(errors),
            )

        # Transition to confirmed status
        conn.execute(
            """
            UPDATE receipts
            SET status = 'confirmed',
                confirmed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP,
                flags_json = '[]'
            WHERE id = ?;
            """,
            (receipt_id,),
        )

        conn.execute(
            """
            INSERT INTO receipt_events (receipt_id, event_type, details_json)
            VALUES (?, 'CONFIRMED', ?);
            """,
            (
                receipt_id,
                json.dumps({
                    "vendor": vendor,
                    "receipt_date": receipt_date,
                    "total_paise": total_paise,
                    "category": category,
                }),
            ),
        )

    return get_receipt_details(receipt_id)


def discard_duplicate(receipt_id: str) -> None:
    """Mark duplicate receipt upload as discarded."""
    with get_db() as conn:
        conn.execute(
            "UPDATE receipts SET status = 'discarded_duplicate', updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
            (receipt_id,),
        )
        conn.execute(
            "INSERT INTO receipt_events (receipt_id, event_type, details_json) VALUES (?, 'DISCARDED_DUPLICATE', NULL);",
            (receipt_id,),
        )


def keep_separate(receipt_id: str) -> dict:
    """Reset potential duplicate upload to needs_review as a distinct expense."""
    with get_db() as conn:
        row = conn.execute("SELECT flags_json FROM receipts WHERE id = ?;", (receipt_id,)).fetchone()
        flags = [f for f in json.loads(row["flags_json"] or "[]") if f != "duplicate"] if row else []
        conn.execute(
            """
            UPDATE receipts
            SET duplicate_of_receipt_id = NULL,
                status = 'needs_review',
                flags_json = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (json.dumps(flags), receipt_id),
        )
        conn.execute(
            "INSERT INTO receipt_events (receipt_id, event_type, details_json) VALUES (?, 'KEPT_SEPARATE', NULL);",
            (receipt_id,),
        )

    return get_receipt_details(receipt_id)

