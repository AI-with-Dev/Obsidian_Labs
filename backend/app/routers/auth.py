import hashlib
import hmac
import re
import secrets
import sqlite3
import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

import psycopg

from backend.app.database import get_db
from backend.app.models import ApiResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SESSION_COOKIE = "shopledger_session"
SESSION_TTL_SECONDS = 30 * 24 * 60 * 60
PASSWORD_ITERATIONS = 310_000
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _cookie_security(request: Request) -> tuple[bool, str]:
    origin = request.headers.get("origin", "")
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip()
    secure = (
        request.url.scheme == "https"
        or forwarded_proto == "https"
        or origin.startswith("https://")
    )
    return secure, "none" if secure else "lax"


class AccountInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fullName: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    businessName: str = Field(min_length=1, max_length=120)
    phone: str = Field(default="", max_length=40)
    address: str = Field(default="", max_length=300)
    gstin: str = Field(default="", max_length=20)
    password: str = Field(min_length=12, max_length=128)
    passwordConfirmation: str = Field(min_length=12, max_length=128)
    language: Literal["en", "hi"] = "en"
    currency: Literal["INR", "USD", "EUR", "GBP"] = "INR"


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class AccountUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fullName: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, min_length=3, max_length=254)
    businessName: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=300)
    gstin: str | None = Field(default=None, max_length=20)
    language: Literal["en", "hi"] | None = None
    currency: Literal["INR", "USD", "EUR", "GBP"] | None = None
    currentPassword: str | None = Field(default=None, min_length=1, max_length=128)


class PasswordUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currentPassword: str = Field(min_length=1, max_length=128)
    newPassword: str = Field(min_length=12, max_length=128)
    passwordConfirmation: str = Field(min_length=12, max_length=128)


def _account_payload(row) -> dict:
    return {
        "fullName": row["full_name"],
        "email": row["email"],
        "businessName": row["business_name"],
        "phone": row["phone"],
        "address": row["address"],
        "gstin": row["gstin"],
        "language": row["language"],
        "currency": row["currency"],
    }


def _account_by_id(owner_id: int) -> dict:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM shop_owner WHERE id = ?", (owner_id,)).fetchone()
    return _account_payload(row)


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(actual.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _password_policy_error(password: str) -> str | None:
    requirements = (
        (len(password) >= 12, "Password must contain at least 12 characters."),
        (any(char.islower() for char in password), "Password must include a lowercase letter."),
        (any(char.isupper() for char in password), "Password must include an uppercase letter."),
        (any(char.isdigit() for char in password), "Password must include a number."),
        (any(not char.isalnum() for char in password), "Password must include a symbol."),
    )
    return next((message for valid, message in requirements if not valid), None)


def _new_session(owner_id: int, response: Response, request: Request) -> None:
    token = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + SESSION_TTL_SECONDS
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    secure, samesite = _cookie_security(request)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO login_sessions(token_hash, owner_id, expires_at) VALUES (?, ?, ?)",
            (token_hash, owner_id, expires_at),
        )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/api",
    )


def _session_owner(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = int(time.time())
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT owner.*
            FROM login_sessions AS session
            JOIN shop_owner AS owner ON owner.id = session.owner_id
            WHERE session.token_hash = ? AND session.expires_at > ?
            """,
            (token_hash, now),
        ).fetchone()
        if row is None:
            conn.execute("DELETE FROM login_sessions WHERE expires_at <= ?", (now,))
            return None
        return {"id": row["id"], **_account_payload(row)}


def require_authenticated_owner(request: Request) -> dict:
    owner = _session_owner(request)
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in to continue.",
        )
    return owner


@router.get("/status", response_model=ApiResponse[dict])
async def auth_status(request: Request):
    owner = _session_owner(request)
    with get_db() as conn:
        configured = conn.execute("SELECT 1 FROM shop_owner LIMIT 1").fetchone() is not None
    return ApiResponse.ok({
        "configured": configured,
        "authenticated": owner is not None,
        "account": {key: value for key, value in owner.items() if key != "id"} if owner else None,
    })


@router.post("/setup", response_model=ApiResponse[dict], status_code=201)
async def setup_account(payload: AccountInput, request: Request, response: Response):
    if not payload.fullName.strip() or not payload.businessName.strip():
        raise HTTPException(status_code=400, detail="Name and business name are required.")
    if not EMAIL_PATTERN.fullmatch(payload.email.strip()):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    if payload.password != payload.passwordConfirmation:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    policy_error = _password_policy_error(payload.password)
    if policy_error:
        raise HTTPException(status_code=400, detail=policy_error)

    try:
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO shop_owner
                    (full_name, email, password_hash, business_name, phone, address, gstin, language, currency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.fullName.strip(),
                    payload.email.strip().lower(),
                    _hash_password(payload.password),
                    payload.businessName.strip(),
                    payload.phone.strip(),
                    payload.address.strip(),
                    payload.gstin.strip().upper(),
                    payload.language,
                    payload.currency,
                ),
            )
            owner_id = conn.execute("SELECT id FROM shop_owner WHERE email = ?", (payload.email.strip().lower(),)).fetchone()["id"]
    except (sqlite3.IntegrityError, psycopg.IntegrityError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        ) from exc
    except HTTPException:
        raise

    _new_session(owner_id, response, request)
    return ApiResponse.ok({"account": _account_by_id(owner_id)})


@router.post("/login", response_model=ApiResponse[dict])
async def login(payload: LoginInput, request: Request, response: Response):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM shop_owner WHERE LOWER(email) = LOWER(?)",
            (payload.email.strip(),),
        ).fetchone()
    if row is None or not _verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    _new_session(row["id"], response, request)
    return ApiResponse.ok({"account": _account_by_id(row["id"])})


@router.post("/logout", response_model=ApiResponse[dict])
async def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with get_db() as conn:
            conn.execute("DELETE FROM login_sessions WHERE token_hash = ?", (token_hash,))
    secure, samesite = _cookie_security(request)
    response.delete_cookie(
        SESSION_COOKIE,
        path="/api",
        httponly=True,
        secure=secure,
        samesite=samesite,
    )
    return ApiResponse.ok({"signedOut": True})


@router.get("/me", response_model=ApiResponse[dict])
async def current_account(owner: dict = Depends(require_authenticated_owner)):
    return ApiResponse.ok({key: value for key, value in owner.items() if key != "id"})


@router.patch("/profile", response_model=ApiResponse[dict])
async def update_profile(payload: AccountUpdate, owner: dict = Depends(require_authenticated_owner)):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return ApiResponse.ok(owner)
    current_password = updates.pop("currentPassword", None)
    if not updates:
        return ApiResponse.ok(owner)
    for field in ("fullName", "businessName"):
        if field in updates and updates[field] is not None and not updates[field].strip():
            raise HTTPException(status_code=400, detail=f"{field} cannot be blank.")
    if updates.get("email") is not None:
        updates["email"] = updates["email"].strip().lower()
        if not EMAIL_PATTERN.fullmatch(updates["email"]):
            raise HTTPException(status_code=400, detail="Enter a valid email address.")
        if updates["email"] != owner["email"]:
            with get_db() as conn:
                row = conn.execute(
                    "SELECT password_hash FROM shop_owner WHERE id = ?",
                    (owner["id"],),
                ).fetchone()
            if current_password is None or not _verify_password(current_password, row["password_hash"]):
                raise HTTPException(
                    status_code=400,
                    detail="Enter your current password to change the sign-in email.",
                )
    column_names = {
        "fullName": "full_name",
        "email": "email",
        "businessName": "business_name",
        "phone": "phone",
        "address": "address",
        "gstin": "gstin",
        "language": "language",
        "currency": "currency",
    }
    updates = {key: value for key, value in updates.items() if value is not None}
    if not updates:
        return ApiResponse.ok(owner)
    assignments = ", ".join(f"{column_names[key]} = ?" for key in updates)
    values = [value.strip() if key in {"fullName", "email", "businessName", "phone", "address"} else value
              for key, value in updates.items()]
    try:
        with get_db() as conn:
            values.append(owner["id"])
            conn.execute(
                f"UPDATE shop_owner SET {assignments} WHERE id = ?",
                values,
            )
            row = conn.execute(
                "SELECT * FROM shop_owner WHERE id = ?",
                (owner["id"],),
            ).fetchone()
    except (sqlite3.IntegrityError, psycopg.IntegrityError) as exc:
        raise HTTPException(status_code=409, detail="That email address is already in use.") from exc
    return ApiResponse.ok(_account_payload(row))


@router.post("/password", response_model=ApiResponse[dict])
async def update_password(
    payload: PasswordUpdate,
    request: Request,
    response: Response,
    owner: dict = Depends(require_authenticated_owner),
):
    if payload.newPassword != payload.passwordConfirmation:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    policy_error = _password_policy_error(payload.newPassword)
    if policy_error:
        raise HTTPException(status_code=400, detail=policy_error)
    with get_db() as conn:
        row = conn.execute(
            "SELECT password_hash FROM shop_owner WHERE id = ?",
            (owner["id"],),
        ).fetchone()
        if row is None or not _verify_password(payload.currentPassword, row["password_hash"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")
        conn.execute(
            "UPDATE shop_owner SET password_hash = ? WHERE id = ?",
            (_hash_password(payload.newPassword), owner["id"]),
        )
        conn.execute("DELETE FROM login_sessions WHERE owner_id = ?", (owner["id"],))
    _new_session(owner["id"], response, request)
    return ApiResponse.ok({"passwordChanged": True, "account": owner})
