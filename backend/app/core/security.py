import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Response

# OWASP Password Storage Cheat Sheet baseline for Argon2id: m=19456 KiB
# (19 MiB), t=2, p=1. Deliberately below argon2-cffi's stronger defaults
# (64 MiB/t=3/p=4) to keep per-request cost predictable on a small Lightsail
# instance shared with the app server and SQLite.
_password_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    return True


def needs_rehash(password_hash: str) -> bool:
    return _password_hasher.check_needs_rehash(password_hash)


SESSION_COOKIE_NAME = "session_token"
SESSION_TTL = timedelta(days=7)


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    # Sessions are looked up by this hash, never the raw token, so a DB leak
    # doesn't hand out valid session credentials (same rationale as password
    # hashing, but SHA-256 suffices here since the token is already
    # high-entropy random data, not a low-entropy user-chosen secret).
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_expires_at() -> datetime:
    return datetime.now(UTC) + SESSION_TTL


def set_session_cookie(response: Response, token: str, *, secure: bool) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,
        secure=secure,
        samesite="strict",
    )


def clear_session_cookie(response: Response, *, secure: bool) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=secure,
        samesite="strict",
    )
