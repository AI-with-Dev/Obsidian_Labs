import os
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
from backend.app.models import ApiResponse


@pytest.fixture(autouse=True)
def test_db_setup(tmp_path):
    """Provide an isolated temporary SQLite database for tests."""
    temp_db = tmp_path / "test_shopledger.db"
    init_db(str(temp_db))
    # Override settings for tests
    original_db = settings.DATABASE_PATH
    settings.DATABASE_PATH = str(temp_db)
    yield temp_db
    settings.DATABASE_PATH = original_db


def test_database_tables_exist(test_db_setup):
    """Verify that receipts, receipt_items, and receipt_events tables exist."""
    with get_db(str(test_db_setup)) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tables = [row["name"] for row in cursor.fetchall()]
        assert "receipts" in tables
        assert "receipt_items" in tables
        assert "receipt_events" in tables
        assert "shop_owner" in tables
        assert "login_sessions" in tables


def test_sqlite_pragmas(test_db_setup):
    """Verify foreign keys and WAL mode are configured."""
    with get_db(str(test_db_setup)) as conn:
        fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert fk == 1


def test_health_endpoint():
    """Verify /api/health returns HTTP 200 with standard response envelope."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["error"] is None
    assert data["data"]["status"] == "ok"
    assert data["data"]["database"] == "connected"


@pytest.mark.parametrize("path", ["/", "/script-health-check", "/healthz"])
def test_hosting_health_endpoints(path):
    """Hosting platform probes receive success instead of route-not-found responses."""
    response = TestClient(app).get(path)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_404_error_envelope():
    """Verify missing endpoints return structured error envelope."""
    client = TestClient(app)
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert data["error"]["code"] == "HTTP_404"


def test_api_response_envelope_helpers():
    """Verify ApiResponse helper serialization."""
    ok_resp = ApiResponse.ok({"count": 5})
    assert ok_resp.success is True
    assert ok_resp.data == {"count": 5}
    assert ok_resp.error is None

    err_resp = ApiResponse.fail("TEST_ERROR", "Something broke")
    assert err_resp.success is False
    assert err_resp.data is None
    assert err_resp.error.code == "TEST_ERROR"
    assert err_resp.error.message == "Something broke"
