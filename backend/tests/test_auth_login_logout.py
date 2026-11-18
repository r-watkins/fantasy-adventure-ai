import pytest
from httpx import AsyncClient, Response

from app.core.config import get_settings

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


SUBDIRECTORY = "/fantasy-adventure-ai"
CREDENTIALS = {"email": "scoped@example.com", "password": "correct horse battery"}


def _use_subdirectory_cookie_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SESSION_COOKIE_PATH", SUBDIRECTORY)
    get_settings.cache_clear()


def _session_cookie_headers(response: Response) -> list[str]:
    return [
        header
        for header in response.headers.get_list("set-cookie")
        if header.startswith("session_token=")
    ]


async def test_login_scopes_cookie_and_clears_legacy_cookie_under_subdirectory(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_subdirectory_cookie_path(monkeypatch)
    await client.post("/api/auth/register", json=CREDENTIALS)
    client.cookies.clear()

    response = await client.post("/api/auth/login", json=CREDENTIALS)

    assert response.status_code == 200
    scoped, legacy = _session_cookie_headers(response)
    assert f"Path={SUBDIRECTORY}" in scoped
    assert "Max-Age=0" not in scoped
    assert "Max-Age=0" in legacy
    assert "Path=/;" in legacy


async def test_register_scopes_cookie_and_clears_legacy_cookie_under_subdirectory(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_subdirectory_cookie_path(monkeypatch)

    response = await client.post("/api/auth/register", json=CREDENTIALS)

    assert response.status_code == 201
    scoped, legacy = _session_cookie_headers(response)
    assert f"Path={SUBDIRECTORY}" in scoped
    assert "Max-Age=0" in legacy
    assert "Path=/;" in legacy


async def test_logout_clears_scoped_and_legacy_cookies_under_subdirectory(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_subdirectory_cookie_path(monkeypatch)
    register_response = await client.post("/api/auth/register", json=CREDENTIALS)
    token = register_response.headers["set-cookie"].split("session_token=")[1].split(";")[0]
    # The scoped cookie isn't sent to /api/... by the test client's jar (the
    # real proxy path includes the prefix), so present it explicitly.
    client.cookies.clear()

    response = await client.post("/api/auth/logout", headers={"Cookie": f"session_token={token}"})

    assert response.status_code == 204
    scoped, legacy = _session_cookie_headers(response)
    assert f"Path={SUBDIRECTORY}" in scoped
    assert "Max-Age=0" in scoped
    assert "Max-Age=0" in legacy
    assert "Path=/;" in legacy


async def test_login_at_default_path_sets_a_single_root_cookie(client: AsyncClient) -> None:
    await client.post("/api/auth/register", json=CREDENTIALS)
    client.cookies.clear()

    response = await client.post("/api/auth/login", json=CREDENTIALS)

    (only_cookie,) = _session_cookie_headers(response)
    assert "Path=/;" in only_cookie
    assert "Max-Age=0" not in only_cookie
