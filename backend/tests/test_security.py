import hashlib
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from fastapi import Response

from app.core.security import (
    SESSION_COOKIE_NAME,
    SESSION_TTL,
    clear_session_cookie,
    generate_session_token,
    hash_password,
    hash_session_token,
    needs_rehash,
    session_expires_at,
    set_session_cookie,
    verify_password,
)


def test_hash_password_produces_argon2id_hash() -> None:
    hashed = hash_password("correct horse battery staple")

    assert hashed.startswith("$argon2id$")


def test_hash_password_uses_unique_salt_per_call() -> None:
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")

    assert first != second


def test_verify_password_accepts_correct_password() -> None:
    hashed = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", hashed) is True


def test_verify_password_rejects_incorrect_password() -> None:
    hashed = hash_password("correct horse battery staple")

    assert verify_password("wrong password", hashed) is False


def test_verify_password_rejects_malformed_hash() -> None:
    assert verify_password("anything", "not-a-real-hash") is False


def test_needs_rehash_false_for_current_params() -> None:
    hashed = hash_password("correct horse battery staple")

    assert needs_rehash(hashed) is False


def test_needs_rehash_true_for_weaker_params() -> None:
    weak_hasher = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)
    weak_hash = weak_hasher.hash("correct horse battery staple")

    assert needs_rehash(weak_hash) is True


def test_generate_session_token_is_url_safe_and_high_entropy() -> None:
    token = generate_session_token()

    assert len(token) >= 32
    assert all(c.isalnum() or c in "-_" for c in token)


def test_generate_session_token_is_unique_per_call() -> None:
    assert generate_session_token() != generate_session_token()


def test_hash_session_token_is_deterministic_sha256() -> None:
    token = "some-opaque-token"

    assert hash_session_token(token) == hashlib.sha256(token.encode("utf-8")).hexdigest()


def test_hash_session_token_differs_for_different_tokens() -> None:
    assert hash_session_token("token-a") != hash_session_token("token-b")


def test_session_expires_at_is_roughly_ttl_from_now() -> None:
    before = datetime.now(UTC) + SESSION_TTL
    expiry = session_expires_at()
    after = datetime.now(UTC) + SESSION_TTL

    assert before - timedelta(seconds=1) <= expiry <= after + timedelta(seconds=1)


def test_set_session_cookie_sets_expected_attributes() -> None:
    response = Response()

    set_session_cookie(response, "opaque-token-value", secure=True)

    cookie_header = response.headers["set-cookie"]
    assert f"{SESSION_COOKIE_NAME}=opaque-token-value" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "Secure" in cookie_header
    assert "samesite=strict" in cookie_header.lower()
    assert f"Max-Age={int(SESSION_TTL.total_seconds())}" in cookie_header


def test_set_session_cookie_omits_secure_when_not_secure() -> None:
    response = Response()

    set_session_cookie(response, "opaque-token-value", secure=False)

    cookie_header = response.headers["set-cookie"]
    assert "Secure" not in cookie_header


def test_clear_session_cookie_expires_immediately() -> None:
    response = Response()

    clear_session_cookie(response, secure=True)

    cookie_header = response.headers["set-cookie"]
    assert f"{SESSION_COOKIE_NAME}=" in cookie_header
    assert 'Max-Age=0' in cookie_header
