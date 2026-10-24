import io
import json
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.config import settings
from backend.app.database import get_db, init_db
from backend.app.main import app
from conftest import ensure_test_owner


@pytest.fixture(autouse=True)
def setup_isolated_db(tmp_path):
    """Provide isolated database and storage for tests."""
    temp_db = tmp_path / "test_review.db"
    temp_uploads = tmp_path / "uploads"
    temp_uploads.mkdir(parents=True, exist_ok=True)

    init_db(str(temp_db))
    ensure_test_owner(str(temp_db))

    orig_db = settings.DATABASE_PATH
    orig_up = settings.UPLOAD_DIR

    settings.DATABASE_PATH = str(temp_db)
    settings.UPLOAD_DIR = str(temp_uploads)

    yield temp_db, temp_uploads

    settings.DATABASE_PATH = orig_db
    settings.UPLOAD_DIR = orig_up


def _upload_sample_receipt(client: TestClient) -> str:
    """Helper to upload a sample receipt and return its ID."""
    fake_img = b"\xff\xd8\xff\xe0fake_receipt_bytes"
    res = client.post(
        "/api/receipts/upload",
        files={"file": ("stationery_bill.jpg", io.BytesIO(fake_img), "image/jpeg")},
    )
    assert res.status_code == 200
    return res.json()["data"]["id"]


def test_save_receipt_draft():
    """Verify editing receipt details and saving draft."""
    client = TestClient(app)
    receipt_id = _upload_sample_receipt(client)

    # Save draft edits
    payload = {
        "vendor": "Shree Ganesh Stationery",
        "date": "2026-10-20",
        "currency": "INR",
        "items": [
            {"name": "Classmate Notebooks (Pack of 6)", "amount": 360.50},
            {"name": "Camlin Permanent Marker Black", "amount": 40.00},
        ],
        "total": 400.50,
        "category": "inventory",
    }

    res = client.patch(f"/api/receipts/{receipt_id}", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["id"] == receipt_id
    assert data["vendor"] == "Shree Ganesh Stationery"
    assert data["date"] == "2026-10-20"
    assert data["currency"] == "INR"
    assert data["total"] == 400.50
    assert data["category"] == "inventory"
    assert data["status"] == "draft"
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Classmate Notebooks (Pack of 6)"
    assert data["items"][0]["amount"] == 360.50
    assert data["items"][1]["amount"] == 40.00

    # Verify integer paise in SQLite
    with get_db() as conn:
        row = conn.execute("SELECT total_paise FROM receipts WHERE id = ?;", (receipt_id,)).fetchone()
        assert row["total_paise"] == 40050

        items = conn.execute(
            "SELECT description, line_total_paise FROM receipt_items WHERE receipt_id = ? ORDER BY item_order;",
            (receipt_id,),
        ).fetchall()
        assert items[0]["line_total_paise"] == 36050
        assert items[1]["line_total_paise"] == 4000

        # Verify EDITED audit event
        event = conn.execute(
            "SELECT event_type, details_json FROM receipt_events WHERE receipt_id = ? AND event_type = 'EDITED';",
            (receipt_id,),
        ).fetchone()
        assert event is not None
        details = json.loads(event["details_json"])
        assert details["vendor"] == "Shree Ganesh Stationery"


def test_confirm_receipt_validation_failures():
    """Verify that confirmation rejects receipts with missing or invalid fields."""
    client = TestClient(app)
    receipt_id = _upload_sample_receipt(client)

    # 1. Unfilled receipt (missing vendor, date, total)
    res = client.post(f"/api/receipts/{receipt_id}/confirm")
    assert res.status_code == 400
    err = res.json()["error"]["message"]
    assert "Vendor name is required" in err
    assert "Receipt date is required" in err
    assert "positive amount" in err

    # 2. Invalid date format
    client.patch(
        f"/api/receipts/{receipt_id}",
        json={"vendor": "Agrawal Book Depot", "date": "20-10-2026", "total": 500.0, "category": "inventory"},
    )
    res = client.post(f"/api/receipts/{receipt_id}/confirm")
    assert res.status_code == 400
    assert "YYYY-MM-DD" in res.json()["error"]["message"]

    # 3. Non-positive total
    client.patch(
        f"/api/receipts/{receipt_id}",
        json={"vendor": "Agrawal Book Depot", "date": "2026-10-20", "total": 0.0, "category": "inventory"},
    )
    res = client.post(f"/api/receipts/{receipt_id}/confirm")
    assert res.status_code == 400
    assert "positive amount" in res.json()["error"]["message"]

    # 4. Invalid category rejected
    patch_res = client.patch(
        f"/api/receipts/{receipt_id}",
        json={"vendor": "Agrawal Book Depot", "date": "2026-10-20", "total": 500.0, "category": "crypto_trading"},
    )
    assert patch_res.status_code == 400
    assert "Category must be one of" in patch_res.json()["error"]["message"]


def test_confirm_receipt_success():
    """Verify explicit owner confirmation transitions receipt into confirmed ledger."""
    client = TestClient(app)
    receipt_id = _upload_sample_receipt(client)

    # Fill valid receipt details
    client.patch(
        f"/api/receipts/{receipt_id}",
        json={
            "vendor": "National Paper Co.",
            "date": "2026-10-22",
            "currency": "INR",
            "items": [{"name": "Kraft Paper Roll", "amount": 850.0}],
            "total": 850.0,
            "category": "packaging",
        },
    )

    # Confirm
    res = client.post(f"/api/receipts/{receipt_id}/confirm")
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["status"] == "confirmed"
    assert data["vendor"] == "National Paper Co."
    assert data["total"] == 850.0

    # Verify database state
    with get_db() as conn:
        row = conn.execute("SELECT status, confirmed_at FROM receipts WHERE id = ?;", (receipt_id,)).fetchone()
        assert row["status"] == "confirmed"
        assert row["confirmed_at"] is not None

        # Verify CONFIRMED audit event
        event = conn.execute(
            "SELECT event_type FROM receipt_events WHERE receipt_id = ? AND event_type = 'CONFIRMED';",
            (receipt_id,),
        ).fetchone()
        assert event is not None

    # Idempotent re-confirmation returns confirmed receipt cleanly
    res2 = client.post(f"/api/receipts/{receipt_id}/confirm")
    assert res2.status_code == 200
    assert res2.json()["data"]["status"] == "confirmed"


@pytest.mark.parametrize(
    ("category", "expected_type"),
    [
        ("inventory", "expense"),
        ("retail_sales", "expense"),
    ],
)
def test_manual_receipts_default_to_expense_without_firm_match(category, expected_type):
    """A category alone must never classify a receipt as income."""
    client = TestClient(app)
    receipt_id = _upload_sample_receipt(client)

    response = client.patch(
        f"/api/receipts/{receipt_id}",
        json={
            "vendor": "Example Shop",
            "date": "2026-10-22",
            "total": 100.0,
            "category": category,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["type"] == expected_type
