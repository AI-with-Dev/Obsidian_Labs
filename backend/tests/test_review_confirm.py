import io
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


@pytest.fixture(autouse=True)
def test_setup(tmp_path):
    """Provide isolated SQLite database and upload folder for tests."""
    temp_db = tmp_path / "test_shopledger.db"
    temp_uploads = tmp_path / "uploads"
    temp_uploads.mkdir(parents=True, exist_ok=True)

    init_db(str(temp_db))

    orig_db = settings.DATABASE_PATH
    orig_up = settings.UPLOAD_DIR

    settings.DATABASE_PATH = str(temp_db)
    settings.UPLOAD_DIR = str(temp_uploads)

    yield temp_db, temp_uploads

    settings.DATABASE_PATH = orig_db
    settings.UPLOAD_DIR = orig_up


def test_edit_and_confirm_receipt(test_setup):
    """Test editing receipt details and confirming into ledger."""
    client = TestClient(app)
    fake_png = b"\x89PNG\r\n\x1a\n" + b"dummy_content"

    # 1. Upload receipt
    up_res = client.post(
        "/api/receipts/upload",
        files={"file": ("bill.png", io.BytesIO(fake_png), "image/png")},
    )
    assert up_res.status_code == 200
    receipt_id = up_res.json()["data"]["id"]

    # 2. Patch/edit receipt
    patch_payload = {
        "vendor": "Rajesh General Store",
        "date": "2026-10-15",
        "currency": "INR",
        "items": [
            {"name": "A4 Paper Ream", "amount": 350.0},
            {"name": "Blue Ball Pens (Pack of 10)", "amount": 120.0},
        ],
        "total": 470.0,
        "category": "inventory",
    }
    patch_res = client.patch(f"/api/receipts/{receipt_id}", json=patch_payload)
    assert patch_res.status_code == 200
    pdata = patch_res.json()["data"]
    assert pdata["vendor"] == "Rajesh General Store"
    assert pdata["date"] == "2026-10-15"
    assert pdata["total"] == 470.0
    assert len(pdata["items"]) == 2
    assert pdata["status"] == "draft"

    # 3. Confirm receipt
    conf_res = client.post(f"/api/receipts/{receipt_id}/confirm")
    assert conf_res.status_code == 200
    cdata = conf_res.json()["data"]
    assert cdata["status"] == "confirmed"

    # 4. Verify in dashboard summary
    dash_res = client.get("/api/dashboard/summary")
    assert dash_res.status_code == 200
    sdata = dash_res.json()["data"]
    assert sdata["confirmedCount"] == 1
    assert sdata["totalSpent"] == 470.0
    assert sdata["topVendors"][0]["vendor"] == "Rajesh General Store"


def test_confirm_invalid_receipt_fails(test_setup):
    """Test that confirming without valid total fails with HTTP 400."""
    client = TestClient(app)
    fake_png = b"\x89PNG\r\n\x1a\n" + b"dummy"
    up_res = client.post("/api/receipts/upload", files={"file": ("bill.png", io.BytesIO(fake_png), "image/png")})
    receipt_id = up_res.json()["data"]["id"]

    # Try confirming without setting total
    conf_res = client.post(f"/api/receipts/{receipt_id}/confirm")
    assert conf_res.status_code == 400
    assert conf_res.json()["success"] is False


def test_export_pdf_endpoint(test_setup):
    """Test downloading confirmed customer receipts as official PDF."""
    client = TestClient(app)
    fake_png = b"\x89PNG\r\n\x1a\n" + b"dummy"
    up_res = client.post("/api/receipts/upload", files={"file": ("bill.png", io.BytesIO(fake_png), "image/png")})
    receipt_id = up_res.json()["data"]["id"]

    client.patch(f"/api/receipts/{receipt_id}", json={
        "vendor": "Apex Stationery",
        "date": "2026-10-10",
        "total": 1250.0,
        "category": "retail_sales",
        "items": [{"name": "Registers wholesale batch", "amount": 1250.0}],
    })
    client.post(f"/api/receipts/{receipt_id}/confirm")

    pdf_res = client.get("/api/export/pdf")
    assert pdf_res.status_code == 200
    assert "application/pdf" in pdf_res.headers["content-type"]
    assert pdf_res.content.startswith(b"%PDF-1.4")
    assert b"ShopLedger" in pdf_res.content
    assert b"Apex Stationery" in pdf_res.content

