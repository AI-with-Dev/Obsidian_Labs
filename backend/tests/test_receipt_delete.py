import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db, init_db
from backend.app.main import app


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Use isolated database and uploads for each test."""
    test_db = tmp_path / "test_receipt_delete.db"
    test_uploads = tmp_path / "uploads"
    test_uploads.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("backend.app.config.settings.DATABASE_PATH", str(test_db))
    monkeypatch.setattr("backend.app.config.settings.UPLOAD_DIR", str(test_uploads))
    init_db(str(test_db))


client = TestClient(app)


def upload_receipt(contents: bytes = b"receipt bytes") -> str:
    response = client.post(
        "/api/receipts/upload",
        files={"file": ("receipt.png", io.BytesIO(contents), "image/png")},
    )
    assert response.status_code == 200
    return response.json()["data"]["id"]


def test_delete_receipt_removes_record_file_and_items():
    receipt_id = upload_receipt()
    with get_db() as conn:
        file_path = Path(
            conn.execute("SELECT file_path FROM receipts WHERE id = ?;", (receipt_id,)).fetchone()["file_path"]
        )
    assert file_path.is_file()

    client.patch(
        f"/api/receipts/{receipt_id}",
        json={
            "vendor": "Test Vendor",
            "date": "2026-10-24",
            "total": 120.0,
            "category": "inventory",
            "items": [{"name": "Paper", "amount": 120.0}],
        },
    )
    response = client.delete(f"/api/receipts/{receipt_id}")

    assert response.status_code == 200
    assert response.json()["data"] is None
    assert not file_path.exists()
    assert client.get(f"/api/receipts/{receipt_id}").status_code == 404
    assert all(r["id"] != receipt_id for r in client.get("/api/receipts").json()["data"])

    with get_db() as conn:
        assert conn.execute("SELECT 1 FROM receipts WHERE id = ?;", (receipt_id,)).fetchone() is None
        assert conn.execute("SELECT 1 FROM receipt_items WHERE receipt_id = ?;", (receipt_id,)).fetchone() is None


def test_delete_receipt_returns_not_found_for_unknown_id():
    response = client.delete("/api/receipts/missing")

    assert response.status_code == 404
    assert response.json()["success"] is False
