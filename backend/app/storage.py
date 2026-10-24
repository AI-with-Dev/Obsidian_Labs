import logging
from urllib.parse import quote

import httpx
from fastapi import HTTPException, status

from backend.app.config import settings

logger = logging.getLogger("shopledger.storage")


def validate_storage_configuration() -> None:
    has_url = bool(settings.SUPABASE_URL.strip())
    has_key = bool(settings.SUPABASE_SERVICE_ROLE_KEY.strip())
    if has_url != has_key:
        raise RuntimeError(
            "Set both SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to enable Supabase Storage."
        )
    if settings.uses_supabase_database and not has_url:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required when DATABASE_URL is set."
        )


def _headers(content_type: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _url(path: str) -> str:
    project_url = settings.SUPABASE_URL.rstrip("/")
    if project_url.endswith("/rest/v1"):
        project_url = project_url.removesuffix("/rest/v1")
    return f"{project_url}/storage/v1/{path}"


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    try:
        with httpx.Client(timeout=30) as client:
            response = client.request(method, _url(path), headers=_headers(), **kwargs)
    except httpx.HTTPError as exc:
        logger.exception("Supabase Storage request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Receipt storage is temporarily unavailable.",
        ) from exc
    if response.is_error:
        logger.error(
            "Supabase Storage returned HTTP %s for %s",
            response.status_code,
            method,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Receipt storage request failed.",
        )
    return response


def ensure_storage_bucket() -> None:
    if not settings.uses_supabase_storage:
        return

    bucket = quote(settings.SUPABASE_STORAGE_BUCKET, safe="")
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(_url(f"bucket/{bucket}"), headers=_headers())
            if response.status_code == 404:
                response = client.post(
                    _url("bucket"),
                    headers=_headers("application/json"),
                    json={
                        "id": settings.SUPABASE_STORAGE_BUCKET,
                        "name": settings.SUPABASE_STORAGE_BUCKET,
                        "public": False,
                        "file_size_limit": settings.MAX_FILE_SIZE_BYTES,
                    },
                )
                if response.status_code == 409:
                    response = client.get(_url(f"bucket/{bucket}"), headers=_headers())
    except httpx.HTTPError as exc:
        logger.exception("Could not initialize Supabase Storage bucket")
        raise RuntimeError("Supabase Storage is unreachable during startup.") from exc
    if response.is_error:
        logger.error("Supabase Storage bucket setup returned HTTP %s", response.status_code)
        raise RuntimeError("Could not create or verify the Supabase Storage bucket.")
    if response.json().get("public", False):
        raise RuntimeError(
            f"Supabase Storage bucket '{settings.SUPABASE_STORAGE_BUCKET}' must be private."
        )


def upload_object(
    object_key: str,
    content: bytes,
    mime_type: str,
    *,
    upsert: bool = False,
) -> None:
    bucket = quote(settings.SUPABASE_STORAGE_BUCKET, safe="")
    key = quote(object_key, safe="/")
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                _url(f"object/{bucket}/{key}"),
                headers={**_headers(mime_type), "x-upsert": str(upsert).lower()},
                content=content,
            )
    except httpx.HTTPError as exc:
        logger.exception("Supabase Storage upload failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Receipt storage is temporarily unavailable.",
        ) from exc
    if response.is_error:
        logger.error("Supabase Storage upload returned HTTP %s", response.status_code)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Receipt could not be saved to persistent storage.",
        )


def download_object(object_key: str) -> bytes:
    bucket = quote(settings.SUPABASE_STORAGE_BUCKET, safe="")
    key = quote(object_key, safe="/")
    return _request("GET", f"object/{bucket}/{key}").content


def delete_object(object_key: str) -> None:
    bucket = quote(settings.SUPABASE_STORAGE_BUCKET, safe="")
    response = _request("DELETE", f"object/{bucket}", json={"prefixes": [object_key]})
    if response.status_code not in (200, 204):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Receipt was deleted, but its stored file could not be removed.",
        )
