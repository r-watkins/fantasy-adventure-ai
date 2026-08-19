import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_register_creates_user_and_session_cookie(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/register",
        json={"email": "Player@Example.com", "password": "correct horse battery"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "player@example.com"
    assert "id" in body
    assert "password" not in body
    assert "password_hash" not in body

    cookie_header = response.headers["set-cookie"]
    assert "session_token=" in cookie_header
    assert "HttpOnly" in cookie_header
    # Settings default to environment="development" in tests, so the
    # cookie must not claim Secure - it isn't served over TLS here.
    assert "Secure" not in cookie_header


async def test_register_rejects_duplicate_email_case_insensitively(client: AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "password": "correct horse battery"},
    )

    response = await client.post(
        "/api/auth/register",
        json={"email": "DUP@example.com", "password": "another password entirely"},
    )

    assert response.status_code == 409


async def test_register_rejects_short_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/register",
        json={"email": "shortpw@example.com", "password": "short"},
    )

    assert response.status_code == 422


async def test_register_rejects_invalid_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "correct horse battery"},
    )

    assert response.status_code == 422
