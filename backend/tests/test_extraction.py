import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.config import settings
from backend.app.database import get_db, init_db
from backend.app.main import app
from backend.app.services.gemini_service import ReceiptExtractionResult, ExtractedLineItem


@pytest.fixture(autouse=True)
def test_setup(tmp_path):
    """Provide isolated database and storage for tests."""
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


def test_gemini_extraction_flow(test_setup):
    """Test full extraction pipeline with mocked Gemini API response."""
    client = TestClient(app)

    # 1. Upload receipt
    fake_img = b"\xff\xd8\xff\xe0fake_receipt_image"
    up_res = client.post(
        "/api/receipts/upload",
        files={"file": ("stationery_invoice.jpg", io.BytesIO(fake_img), "image/jpeg")},
    )
    assert up_res.status_code == 200
    receipt_id = up_res.json()["data"]["id"]

    # 2. Mock Gemini extraction result
    mock_result = ReceiptExtractionResult(
        vendor="Royal Paper Mart",
        date="2026-10-15",
        currency="INR",
        items=[
            ExtractedLineItem(name="A4 Copier Paper 75gsm (10 reams)", amount=2400.0),
            ExtractedLineItem(name="Gel Pens Blue (Box of 20)", amount=200.0),
        ],
        total=2600.0,
        suggested_category="inventory",
        uncertainty_flags=[],
    )
    mock_raw_json = json.dumps(mock_result.model_dump())

    with patch("backend.app.services.receipt_service.extract_receipt_with_gemini") as mock_extract:
        mock_extract.return_value = (mock_result, mock_raw_json)

        # 3. Call extract endpoint
        ext_res = client.post(f"/api/receipts/{receipt_id}/extract")
        assert ext_res.status_code == 200
        ext_data = ext_res.json()

        assert ext_data["success"] is True
        receipt = ext_data["data"]
        assert receipt["id"] == receipt_id
        assert receipt["vendor"] == "Royal Paper Mart"
        assert receipt["date"] == "2026-10-15"
        assert receipt["total"] == 2600.0
        assert receipt["category"] == "inventory"
        assert receipt["status"] == "draft"  # Mapped from needs_review
        assert len(receipt["items"]) == 2
        assert receipt["items"][0]["name"] == "A4 Copier Paper 75gsm (10 reams)"
        assert receipt["items"][0]["amount"] == 2400.0

    # 4. Verify DB stores total in integer paise
    temp_db, _ = test_setup
    with get_db(str(temp_db)) as conn:
        row = conn.execute("SELECT total_paise, status, raw_extraction_json FROM receipts WHERE id = ?", (receipt_id,)).fetchone()
        assert row["total_paise"] == 260000  # Rs 2600.00 = 260000 paise
        assert row["status"] == "needs_review"
        assert row["raw_extraction_json"] == mock_raw_json

        items = conn.execute("SELECT description, line_total_paise FROM receipt_items WHERE receipt_id = ?", (receipt_id,)).fetchall()
        assert len(items) == 2
        assert items[0]["line_total_paise"] == 240000
        assert items[1]["line_total_paise"] == 20000

    # 5. Verify GET /api/receipts/{id} returns same data
    get_res = client.get(f"/api/receipts/{receipt_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["vendor"] == "Royal Paper Mart"
    assert get_res.json()["data"]["total"] == 2600.0


def test_extraction_failure_handling(test_setup):
    """Test that extraction failures transition status to extraction_failed."""
    client = TestClient(app, raise_server_exceptions=False)

    # Upload
    up_res = client.post(
        "/api/receipts/upload",
        files={"file": ("corrupt.jpg", io.BytesIO(b"\xff\xd8\xff\xe0data"), "image/jpeg")},
    )
    receipt_id = up_res.json()["data"]["id"]

    with patch("backend.app.services.receipt_service.extract_receipt_with_gemini") as mock_extract:
        mock_extract.side_effect = RuntimeError("Gemini connection timed out")

        ext_res = client.post(f"/api/receipts/{receipt_id}/extract")
        assert ext_res.status_code == 500
        assert ext_res.json()["success"] is False

    temp_db, _ = test_setup
    with get_db(str(temp_db)) as conn:
        row = conn.execute("SELECT status FROM receipts WHERE id = ?", (receipt_id,)).fetchone()
        assert row["status"] == "extraction_failed"
