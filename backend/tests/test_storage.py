import httpx
import pytest

from backend.app.config import settings
from backend.app.database import PostgresConnection
from backend.app.storage import (
    delete_object,
    download_object,
    ensure_storage_bucket,
    upload_object,
    validate_storage_configuration,
)


def test_postgres_placeholder_conversion_preserves_quoted_question_marks():
    query = "SELECT '?' AS literal, col FROM table WHERE a = ? AND b = \"?\""
    assert PostgresConnection._postgres_placeholders(query) == (
        "SELECT '?' AS literal, col FROM table WHERE a = %s AND b = \"?\""
    )


def test_storage_configuration_requires_complete_credentials(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")

    with pytest.raises(RuntimeError, match="Set both SUPABASE_URL"):
        validate_storage_configuration()


def test_supabase_storage_bucket_and_object_operations(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "server-only-test-key")
    monkeypatch.setattr(settings, "SUPABASE_STORAGE_BUCKET", "receipt-files")

    calls = []

    def handle_request(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/bucket/receipt-files") and request.method == "GET":
            if len([call for call in calls if call.method == "GET"]) == 1:
                return httpx.Response(404)
            return httpx.Response(200, json={"id": "receipt-files", "public": False})
        if request.url.path.endswith("/bucket") and request.method == "POST":
            assert request.read()
            return httpx.Response(200, json={"name": "receipt-files", "public": False})
        if request.method == "POST":
            assert request.content == b"receipt bytes"
            assert request.headers["x-upsert"] == "false"
            return httpx.Response(200, json={"Key": "receipt-files/1/receipt.png"})
        if request.method == "GET":
            return httpx.Response(200, content=b"receipt bytes")
        if request.method == "DELETE":
            assert b"1/receipt.png" in request.read()
            return httpx.Response(200, json={"message": "deleted"})
        raise AssertionError(f"Unexpected storage request: {request.method} {request.url}")

    transport = httpx.MockTransport(handle_request)
    client_type = httpx.Client
    monkeypatch.setattr(
        "backend.app.storage.httpx.Client",
        lambda **kwargs: client_type(transport=transport, **kwargs),
    )

    ensure_storage_bucket()
    upload_object("1/receipt.png", b"receipt bytes", "image/png")
    assert download_object("1/receipt.png") == b"receipt bytes"
    delete_object("1/receipt.png")
    assert all(call.headers["apikey"] == "server-only-test-key" for call in calls)
    assert all(
        call.headers["authorization"] == "Bearer server-only-test-key"
        for call in calls
    )
