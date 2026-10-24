import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.config import settings
from backend.app.database import get_db, init_db
from backend.app.main import app
from conftest import ensure_test_owner
from backend.app.routers.auth import require_authenticated_owner
from fastapi import HTTPException
from backend.app.services.gemini_service import (
    ExtractedLineItem,
    ReceiptExtractionResult,
    extract_receipt_with_gemini,
    get_gemini_client,
)


def test_gemini_client_reports_missing_environment_key(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", " \n ")

    with pytest.raises(HTTPException) as exc_info:
        get_gemini_client()

    assert "GEMINI_API_KEY" in exc_info.value.detail
    assert ".env file" in exc_info.value.detail


def test_gemini_client_trims_environment_key(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "  test-gemini-key\n")
    with patch("backend.app.services.gemini_service.genai.Client") as client:
        get_gemini_client()

    client.assert_called_once_with(api_key="test-gemini-key")


def test_extraction_falls_back_from_configured_model_to_supported_flash_lite(
    tmp_path, monkeypatch
):
    receipt_path = tmp_path / "receipt.jpg"
    receipt_path.write_bytes(b"\xff\xd8\xfftest")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "retired-model")
    client = MagicMock()
    client.models.generate_content.side_effect = [
        RuntimeError("model not found"),
        SimpleNamespace(text="{}"),
    ]

    with (
        patch("backend.app.services.gemini_service.genai.Client", return_value=client),
        patch("backend.app.services.gemini_service.time.sleep"),
    ):
        extraction, raw_json = extract_receipt_with_gemini(receipt_path, "image/jpeg")

    assert raw_json == "{}"
    assert extraction.vendor == ""
    called_models = [
        call.kwargs["model"]
        for call in client.models.generate_content.call_args_list
    ]
    assert called_models == ["retired-model", "gemini-3.5-flash-lite"]


@pytest.fixture(autouse=True)
def test_setup(tmp_path):
    """Provide isolated database and storage for tests."""
    temp_db = tmp_path / "test_shopledger.db"
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


@pytest.mark.parametrize(
    ("firm_name", "category", "expected_type", "expected_party"),
    [
        ("SHARMA-STATIONERY!", "retail_sales", "income", "Asha Customer"),
        ("Other Paper Mart", "retail_sales", "expense", "Other Paper Mart"),
    ],
)
def test_extraction_direction_matches_owner_business_name(
    test_setup, firm_name, category, expected_type, expected_party
):
    """Only receipts issued by the owner's firm are income, regardless of category."""
    client = TestClient(app)
    upload = client.post(
        "/api/receipts/upload",
        files={"file": ("receipt.jpg", io.BytesIO(b"\xff\xd8\xffowner-match-test"), "image/jpeg")},
    )
    receipt_id = upload.json()["data"]["id"]
    extraction = ReceiptExtractionResult(
        vendor=firm_name,
        firm_name=firm_name,
        customer_name="Asha Customer",
        date="2026-10-15",
        total=250.0,
        suggested_category=category,
    )
    prior_override = app.dependency_overrides[require_authenticated_owner]
    app.dependency_overrides[require_authenticated_owner] = lambda: {
        "id": 1,
        "businessName": "Sharma Stationery",
    }
    try:
        with patch("backend.app.services.receipt_service.extract_receipt_with_gemini") as mock_extract:
            mock_extract.return_value = (extraction, json.dumps(extraction.model_dump()))
            response = client.post(f"/api/receipts/{receipt_id}/extract")
    finally:
        app.dependency_overrides[require_authenticated_owner] = prior_override

    assert response.status_code == 200
    receipt = response.json()["data"]
    assert receipt["type"] == expected_type
    assert receipt["vendor"] == expected_party


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


def test_extraction_unstructured_handwritten_notes(test_setup):
    """Test extracting informal local notes like 'Ramesh 20 rupay kurkure' and 'Suresh bhai 500 jama'."""
    client = TestClient(app)

    # Note 1: Suresh bhai 500 jama (Money Received)
    up1 = client.post(
        "/api/receipts/upload",
        files={"file": ("note_jama.jpg", io.BytesIO(b"\xff\xd8\xffsuresh_jama"), "image/jpeg")},
    )
    r1_id = up1.json()["data"]["id"]
    note1 = ReceiptExtractionResult(
        party_name="Suresh Bhai",
        customer_name="Suresh Bhai",
        total=500.0,
        items=[],
        transaction_type="income",
    )
    with patch("backend.app.services.receipt_service.extract_receipt_with_gemini") as mock_extract:
        mock_extract.return_value = (note1, json.dumps(note1.model_dump()))
        res1 = client.post(f"/api/receipts/{r1_id}/extract")
        assert res1.status_code == 200
        d1 = res1.json()["data"]
        assert d1["vendor"] == "Suresh Bhai"
        assert d1["total"] == 500.0
        assert d1["type"] == "income"
        assert len(d1["items"]) == 1
        assert "Cash" in d1["items"][0]["name"] or "Jama" in d1["items"][0]["name"]

    # Note 2: Ramesh 20 rupay kurkure (Borrowed items / Credit Udhar)
    up2 = client.post(
        "/api/receipts/upload",
        files={"file": ("note_udhar.jpg", io.BytesIO(b"\xff\xd8\xfframesh_kurkure"), "image/jpeg")},
    )
    r2_id = up2.json()["data"]["id"]
    note2 = ReceiptExtractionResult(
        party_name="Ramesh",
        total=20.0,
        items=[ExtractedLineItem(name="Kurkure", amount=20.0)],
        transaction_type="expense",
    )
    with patch("backend.app.services.receipt_service.extract_receipt_with_gemini") as mock_extract:
        mock_extract.return_value = (note2, json.dumps(note2.model_dump()))
        res2 = client.post(f"/api/receipts/{r2_id}/extract")
        assert res2.status_code == 200
        d2 = res2.json()["data"]
        assert d2["vendor"] == "Ramesh"
        assert d2["total"] == 20.0
        assert d2["type"] == "expense"
        assert d2["items"][0]["name"] == "Kurkure"
