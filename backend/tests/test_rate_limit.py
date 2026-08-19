import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_register_is_rate_limited_after_threshold(client: AsyncClient) -> None:
    for i in range(3):
        response = await client.post(
            "/api/auth/register",
            json={"email": f"ratelimit{i}@example.com", "password": "correct horse battery"},
        )
        assert response.status_code == 201
        client.cookies.clear()

    fourth = await client.post(
        "/api/auth/register",
        json={"email": "ratelimit3@example.com", "password": "correct horse battery"},
    )

    assert fourth.status_code == 429


async def test_login_is_rate_limited_after_threshold(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/auth/register",
        json={"email": "loginlimit@example.com", "password": "correct horse battery"},
    )
    assert register_response.status_code == 201
    client.cookies.clear()

    for _ in range(5):
        response = await client.post(
            "/api/auth/login",
            json={"email": "loginlimit@example.com", "password": "wrong password"},
        )
        assert response.status_code == 401

    sixth = await client.post(
        "/api/auth/login",
        json={"email": "loginlimit@example.com", "password": "wrong password"},
    )

    assert sixth.status_code == 429
