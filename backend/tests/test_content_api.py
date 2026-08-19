import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _register(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/auth/register", json={"email": email, "password": "correct horse battery"}
    )
    assert response.status_code == 201


async def test_list_origins_returns_seeded_origins(client: AsyncClient) -> None:
    await _register(client, "content-origins@example.com")

    response = await client.get("/api/content/origins")

    assert response.status_code == 200
    origin_ids = {origin["id"] for origin in response.json()}
    assert {"tavern_cook", "wheat_farmer"} <= origin_ids


async def test_list_items_returns_seeded_items(client: AsyncClient) -> None:
    await _register(client, "content-items@example.com")

    response = await client.get("/api/content/items")

    assert response.status_code == 200
    items = response.json()
    assert len(items) > 0
    assert all({"id", "name", "category", "rarity", "description"} <= item.keys() for item in items)


async def test_list_origins_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/content/origins")

    assert response.status_code == 401


async def test_list_items_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/content/items")

    assert response.status_code == 401
