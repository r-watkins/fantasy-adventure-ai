import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _register(
    client: AsyncClient,
    email: str = "player@example.com",
    password: str = "correct horse battery",
) -> None:
    response = await client.post(
        "/api/auth/register", json={"email": email, "password": password}
    )
    assert response.status_code == 201
    client.cookies.clear()


async def test_login_succeeds_with_correct_credentials(client: AsyncClient) -> None:
    await _register(client)

    response = await client.post(
        "/api/auth/login",
        json={"email": "player@example.com", "password": "correct horse battery"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "player@example.com"
    assert "session_token=" in response.headers["set-cookie"]


async def test_login_rejects_wrong_password_with_generic_error(client: AsyncClient) -> None:
    await _register(client)

    response = await client.post(
        "/api/auth/login",
        json={"email": "player@example.com", "password": "totally wrong password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


async def test_login_rejects_unknown_email_with_same_generic_error(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "whatever password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


async def test_login_is_case_insensitive_on_email(client: AsyncClient) -> None:
    await _register(client)

    response = await client.post(
        "/api/auth/login",
        json={"email": "Player@Example.com", "password": "correct horse battery"},
    )

    assert response.status_code == 200


async def test_logout_revokes_session_cookie(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/auth/register",
        json={"email": "logout@example.com", "password": "correct horse battery"},
    )
    assert register_response.status_code == 201
    original_token = client.cookies["session_token"]

    logout_response = await client.post("/api/auth/logout")
    assert logout_response.status_code == 204

    cookie_header = logout_response.headers["set-cookie"]
    assert "session_token=" in cookie_header
    assert "Max-Age=0" in cookie_header

    # The revoked session must no longer authorize anything - replay the
    # original (now-revoked) token explicitly, since httpx's cookie jar
    # already dropped it client-side after the Max-Age=0 response above.
    client.cookies.set("session_token", original_token)
    second_logout = await client.post("/api/auth/logout")
    assert second_logout.status_code == 401


async def test_logout_without_session_cookie_is_unauthorized(client: AsyncClient) -> None:
    response = await client.post("/api/auth/logout")

    assert response.status_code == 401
