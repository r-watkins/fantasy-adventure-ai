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


async def test_turn_submission_is_rate_limited_after_threshold(client: AsyncClient) -> None:
    # Task 55: the source design doc calls for "turn rate-limiting hooks"
    # specifically (not just auth) - each turn costs a real Gemini API call
    # in production, so an unbounded client could otherwise run up real
    # cost. 20/minute per IP is generous for real gameplay pacing while
    # still capping a scripted abuse loop.
    register_response = await client.post(
        "/api/auth/register",
        json={"email": "turnlimit@example.com", "password": "correct horse battery"},
    )
    assert register_response.status_code == 201

    create_response = await client.post(
        "/api/saves", json={"origin_id": "tavern_cook", "character_name": "Avery"}
    )
    assert create_response.status_code == 201
    save_id = create_response.json()["id"]

    for _ in range(20):
        response = await client.post(
            f"/api/saves/{save_id}/turns", json={"message": "I look around."}
        )
        assert response.status_code == 200

    twenty_first = await client.post(
        f"/api/saves/{save_id}/turns", json={"message": "I look around."}
    )

    assert twenty_first.status_code == 429
