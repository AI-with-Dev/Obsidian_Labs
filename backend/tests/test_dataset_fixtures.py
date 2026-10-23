import hashlib
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.database import init_db
from backend.app.main import app

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data/test_fixtures"
GROUND_TRUTH_PATH = FIXTURES_DIR / "ground_truth.json"


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Ensure an isolated database for fixture testing."""
    test_db = tmp_path / "test_fixtures.db"
    test_uploads = tmp_path / "uploads"
    test_uploads.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("backend.app.config.settings.DATABASE_PATH", str(test_db))
    monkeypatch.setattr("backend.app.config.settings.UPLOAD_DIR", str(test_uploads))
    init_db(str(test_db))


@pytest.fixture
def client():
    return TestClient(app)


def test_fixtures_completeness_and_ground_truth():
    """Verify that exactly 20 synthetic receipt fixtures exist and match ground_truth.json."""
    assert GROUND_TRUTH_PATH.exists(), "ground_truth.json must exist in test_fixtures"

    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    assert len(ground_truth) == 20, f"Expected 20 fixtures, found {len(ground_truth)}"

    types_count = {}
    for entry in ground_truth:
        filename = entry["filename"]
        file_path = FIXTURES_DIR / filename
        assert file_path.exists(), f"Fixture file {filename} is missing"
        assert file_path.stat().st_size > 0, f"Fixture file {filename} is empty"

        ftype = entry["type"]
        types_count[ftype] = types_count.get(ftype, 0) + 1

    # Verify edge cases are covered
    assert types_count.get("clear_image") == 8
    assert types_count.get("short_pdf") == 4
    assert any("blurry" in k or "faint" in k or "ambiguous" in k for k in types_count)
    assert any("duplicate" in k for k in types_count)
    assert any("incomplete" in k for k in types_count)


def test_sha256_exact_duplicate_fixture():
    """Verify fixture_16_exact_dup.png is bit-for-bit identical to fixture_03_clear.png."""
    file1 = FIXTURES_DIR / "fixture_03_clear.png"
    file2 = FIXTURES_DIR / "fixture_16_exact_dup.png"

    hash1 = hashlib.sha256(file1.read_bytes()).hexdigest()
    hash2 = hashlib.sha256(file2.read_bytes()).hexdigest()

    assert hash1 == hash2, "Exact duplicate fixture must share identical SHA-256 hash"


def test_upload_fixtures_flow(client):
    """Test uploading representative image and PDF fixtures through upload endpoint."""
    # 1. Upload clear image
    img_path = FIXTURES_DIR / "fixture_01_clear.png"
    with open(img_path, "rb") as f:
        res1 = client.post(
            "/api/receipts/upload",
            files={"file": ("fixture_01_clear.png", f, "image/png")},
        )
    assert res1.status_code == 200
    assert res1.json()["success"] is True
    id1 = res1.json()["data"]["id"]
    assert id1.startswith("rec_")

    # 2. Upload short PDF
    pdf_path = FIXTURES_DIR / "fixture_09_pdf.pdf"
    with open(pdf_path, "rb") as f:
        res2 = client.post(
            "/api/receipts/upload",
            files={"file": ("fixture_09_pdf.pdf", f, "application/pdf")},
        )
    assert res2.status_code == 200
    assert res2.json()["success"] is True
    id2 = res2.json()["data"]["id"]
    assert id2.startswith("rec_")

    # 3. Upload original then exact duplicate
    orig_path = FIXTURES_DIR / "fixture_03_clear.png"
    with open(orig_path, "rb") as f:
        res3 = client.post(
            "/api/receipts/upload",
            files={"file": ("fixture_03_clear.png", f, "image/png")},
        )
    id3 = res3.json()["data"]["id"]

    dup_path = FIXTURES_DIR / "fixture_16_exact_dup.png"
    with open(dup_path, "rb") as f:
        res4 = client.post(
            "/api/receipts/upload",
            files={"file": ("fixture_16_exact_dup.png", f, "image/png")},
        )
    id4 = res4.json()["data"]["id"]

    # Details of id4 should show status duplicate and duplicateOfId pointing to id3
    details = client.get(f"/api/receipts/{id4}").json()["data"]
    assert details["status"] == "duplicate"
    assert details["duplicateOfId"] == id3
    assert "duplicate" in details["flags"]
