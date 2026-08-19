import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_get_me_returns_current_user_when_authenticated(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/auth/register",
        json={"email": "me@example.com", "password": "correct horse battery"},
    )
    assert register_response.status_code == 201
    registered_id = register_response.json()["id"]

    response = await client.get("/api/me")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == registered_id
    assert body["email"] == "me@example.com"
    assert "password" not in body
    assert "password_hash" not in body


async def test_get_me_without_session_cookie_is_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/me")

    assert response.status_code == 401


async def test_get_me_with_revoked_session_is_unauthorized(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/auth/register",
        json={"email": "revoked@example.com", "password": "correct horse battery"},
    )
    assert register_response.status_code == 201
    revoked_token = client.cookies["session_token"]

    logout_response = await client.post("/api/auth/logout")
    assert logout_response.status_code == 204

    # Replay the now-revoked token explicitly - httpx's jar already dropped
    # it client-side from the logout response's Max-Age=0 cookie.
    client.cookies.set("session_token", revoked_token)
    response = await client.get("/api/me")

    assert response.status_code == 401
