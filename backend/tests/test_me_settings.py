import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_get_me_includes_default_theme_preference(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/auth/register",
        json={"email": "theme@example.com", "password": "correct horse battery"},
    )
    assert register_response.status_code == 201

    response = await client.get("/api/me")

    assert response.status_code == 200
    assert response.json()["theme_preference"] == "system"


async def test_put_settings_updates_theme_preference(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/auth/register",
        json={"email": "theme2@example.com", "password": "correct horse battery"},
    )
    assert register_response.status_code == 201

    put_response = await client.put("/api/me/settings", json={"theme_preference": "dark"})
    assert put_response.status_code == 200
    assert put_response.json()["theme_preference"] == "dark"

    get_response = await client.get("/api/me")
    assert get_response.json()["theme_preference"] == "dark"


async def test_put_settings_rejects_invalid_theme(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/auth/register",
        json={"email": "theme3@example.com", "password": "correct horse battery"},
    )
    assert register_response.status_code == 201

    response = await client.put("/api/me/settings", json={"theme_preference": "not-a-theme"})

    assert response.status_code == 422


async def test_put_settings_requires_authentication(client: AsyncClient) -> None:
    response = await client.put("/api/me/settings", json={"theme_preference": "dark"})

    assert response.status_code == 401


async def test_theme_preference_persists_across_login_sessions(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/auth/register",
        json={"email": "theme-persist@example.com", "password": "correct horse battery"},
    )
    assert register_response.status_code == 201

    put_response = await client.put("/api/me/settings", json={"theme_preference": "light"})
    assert put_response.status_code == 200

    logout_response = await client.post("/api/auth/logout")
    assert logout_response.status_code == 204

    login_response = await client.post(
        "/api/auth/login",
        json={"email": "theme-persist@example.com", "password": "correct horse battery"},
    )
    assert login_response.status_code == 200

    get_response = await client.get("/api/me")
    assert get_response.json()["theme_preference"] == "light"
