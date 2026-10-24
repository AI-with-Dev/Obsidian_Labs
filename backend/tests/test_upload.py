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
from conftest import ensure_test_owner


@pytest.fixture(autouse=True)
def test_setup(tmp_path):
    """Provide isolated SQLite database and upload folder for tests."""
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


def test_upload_valid_jpg(test_setup):
    """Test successful JPG receipt upload."""
    client = TestClient(app)
    fake_jpg = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"fake_jpg_content_12345"

    response = client.post(
        "/api/receipts/upload",
        files={"file": ("stationery_bill.jpg", io.BytesIO(fake_jpg), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["error"] is None
    receipt_id = data["data"]["id"]
    assert receipt_id.startswith("rec_")

    # Verify DB record
    temp_db, temp_uploads = test_setup
    with get_db(str(temp_db)) as conn:
        row = conn.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,)).fetchone()
        assert row is not None
        assert row["mime_type"] == "image/jpeg"
        assert row["status"] == "uploaded"
        assert row["file_name"] == "stationery_bill.jpg"
        assert Path(row["file_path"]).is_file()

        event = conn.execute("SELECT * FROM receipt_events WHERE receipt_id = ?", (receipt_id,)).fetchone()
        assert event is not None
        assert event["event_type"] == "UPLOADED"


def test_upload_valid_png(test_setup):
    """Test successful PNG receipt upload."""
    client = TestClient(app)
    fake_png = b"\x89PNG\r\n\x1a\n" + b"fake_png_data"

    response = client.post(
        "/api/receipts/upload",
        files={"file": ("sharma_invoice.png", io.BytesIO(fake_png), "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    receipt_id = data["data"]["id"]

    temp_db, _ = test_setup
    with get_db(str(temp_db)) as conn:
        row = conn.execute("SELECT mime_type FROM receipts WHERE id = ?", (receipt_id,)).fetchone()
        assert row["mime_type"] == "image/png"


def test_upload_valid_pdf(test_setup):
    """Test successful PDF receipt upload."""
    client = TestClient(app)
    fake_pdf = b"%PDF-1.4 fake_pdf_data"

    response = client.post(
        "/api/receipts/upload",
        files={"file": ("wholesale_bill.pdf", io.BytesIO(fake_pdf), "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    receipt_id = data["data"]["id"]

    temp_db, _ = test_setup
    with get_db(str(temp_db)) as conn:
        row = conn.execute("SELECT mime_type FROM receipts WHERE id = ?", (receipt_id,)).fetchone()
        assert row["mime_type"] == "application/pdf"


def test_stream_receipt_file(test_setup):
    """Test retrieving and streaming an uploaded receipt file."""
    client = TestClient(app)
    fake_content = b"\xff\xd8\xff\xe0test_stream_data_bytes"

    # Upload first
    up_res = client.post(
        "/api/receipts/upload",
        files={"file": ("receipt.jpg", io.BytesIO(fake_content), "image/jpeg")},
    )
    receipt_id = up_res.json()["data"]["id"]

    # Retrieve
    get_res = client.get(f"/api/receipts/{receipt_id}/file")
    assert get_res.status_code == 200
    assert get_res.headers["content-type"].startswith("image/jpeg")
    assert get_res.content == fake_content


def test_reject_unsupported_file_type():
    """Test that unsupported file extensions or MIME types are rejected."""
    client = TestClient(app)
    bad_file = b"malicious binary or text file"

    response = client.post(
        "/api/receipts/upload",
        files={"file": ("invoice.exe", io.BytesIO(bad_file), "application/octet-stream")},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "HTTP_400"
    assert "Unsupported file type" in data["error"]["message"]


def test_reject_empty_file():
    """Test that empty uploads are rejected."""
    client = TestClient(app)

    response = client.post(
        "/api/receipts/upload",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "empty" in data["error"]["message"].lower()


def test_get_nonexistent_receipt_file():
    """Test 404 when requesting file for missing receipt ID."""
    client = TestClient(app)
    response = client.get("/api/receipts/rec_nonexistent/file")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "HTTP_404"
