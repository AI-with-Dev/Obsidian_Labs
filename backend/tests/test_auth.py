import sys
from pathlib import Path

from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.main import app


PASSWORD = "StrongPass123!"
NEW_PASSWORD = "EvenStronger456!"
ACCOUNT = {
    "fullName": "Asha Sharma",
    "email": "asha@example.com",
    "businessName": "Sharma Stationery",
    "phone": "+91 9876543210",
    "address": "Pune, Maharashtra",
    "gstin": "27ABCDE1234F1Z5",
    "password": PASSWORD,
    "passwordConfirmation": PASSWORD,
    "language": "hi",
    "currency": "INR",
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "auth_shopledger.db"
    monkeypatch.setattr(settings, "DATABASE_PATH", str(database_path))
    init_db(str(database_path))
    with TestClient(app) as test_client:
        yield test_client


def create_account(client: TestClient) -> dict:
    response = client.post("/api/auth/setup", json=ACCOUNT)
    assert response.status_code == 201
    return response.json()["data"]["account"]


def test_first_run_setup_and_login_protection(client):
    assert client.get("/api/auth/status").json()["data"] == {
        "configured": False,
        "authenticated": False,
        "account": None,
    }
    protected = client.get("/api/dashboard/summary")
    assert protected.status_code == 401
    assert protected.json()["error"]["code"] == "HTTP_401"
    assert client.get("/api/export/pdf").status_code == 401
    assert client.get("/api/export/csv").status_code == 401

    response = client.post("/api/auth/setup", json=ACCOUNT)
    assert response.status_code == 201
    account = response.json()["data"]["account"]
    assert account["fullName"] == ACCOUNT["fullName"]
    assert account["language"] == "hi"
    assert account["currency"] == "INR"
    session_cookie = next(cookie for cookie in client.cookies.jar if cookie.name == "shopledger_session")
    assert "HttpOnly" in session_cookie._rest
    assert session_cookie._rest.get("SameSite") == "strict"
    assert client.get("/api/dashboard/summary").status_code == 200

    setup_again = client.post("/api/auth/setup", json=ACCOUNT)
    assert setup_again.status_code == 409

    client.post("/api/auth/logout")
    assert client.get("/api/receipts").status_code == 401
    logged_in = client.post(
        "/api/auth/login",
        json={"email": ACCOUNT["email"], "password": PASSWORD},
    )
    assert logged_in.status_code == 200
    assert logged_in.json()["data"]["account"]["email"] == ACCOUNT["email"]


@pytest.mark.parametrize(
    ("changes", "expected_status"),
    [
        ({"passwordConfirmation": "DifferentPass456!"}, 400),
        ({"password": "weak", "passwordConfirmation": "weak"}, 422),
    ],
)
def test_setup_rejects_invalid_passwords(client, changes, expected_status):
    response = client.post("/api/auth/setup", json={**ACCOUNT, **changes})
    assert response.status_code == expected_status
    assert client.get("/api/auth/status").json()["data"]["configured"] is False


def test_login_profile_preferences_and_password_rotation(client):
    create_account(client)
    bad_login = client.post(
        "/api/auth/login",
        json={"email": ACCOUNT["email"], "password": "IncorrectPassword1!"},
    )
    assert bad_login.status_code == 401

    updated = client.patch(
        "/api/auth/profile",
        json={
            "businessName": "Asha's Books",
            "language": "en",
            "currency": "USD",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["businessName"] == "Asha's Books"
    assert updated.json()["data"]["language"] == "en"
    assert updated.json()["data"]["currency"] == "USD"
    email_change_without_password = client.patch(
        "/api/auth/profile",
        json={"email": "asha.new@example.com"},
    )
    assert email_change_without_password.status_code == 400
    email_change = client.patch(
        "/api/auth/profile",
        json={"email": "asha.new@example.com", "currentPassword": PASSWORD},
    )
    assert email_change.status_code == 200
    assert email_change.json()["data"]["email"] == "asha.new@example.com"

    other_session = TestClient(app)
    assert other_session.post(
        "/api/auth/login",
        json={"email": "asha.new@example.com", "password": PASSWORD},
    ).status_code == 200

    mismatch = client.post(
        "/api/auth/password",
        json={
            "currentPassword": PASSWORD,
            "newPassword": NEW_PASSWORD,
            "passwordConfirmation": "OtherStrong789!",
        },
    )
    assert mismatch.status_code == 400

    changed = client.post(
        "/api/auth/password",
        json={
            "currentPassword": PASSWORD,
            "newPassword": NEW_PASSWORD,
            "passwordConfirmation": NEW_PASSWORD,
        },
    )
    assert changed.status_code == 200
    assert client.get("/api/dashboard/summary").status_code == 200
    assert other_session.get("/api/dashboard/summary").status_code == 401

    assert client.post(
        "/api/auth/login",
        json={"email": "asha.new@example.com", "password": PASSWORD},
    ).status_code == 401
    assert client.post(
        "/api/auth/login",
        json={"email": "asha.new@example.com", "password": NEW_PASSWORD},
    ).status_code == 200
    other_session.close()


def test_authenticated_csv_export(client):
    create_account(client)
    response = client.get("/api/export/csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text.startswith("Vendor,Date,Category,Currency,Total")
