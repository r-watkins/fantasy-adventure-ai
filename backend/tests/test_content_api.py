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


async def test_list_locations_returns_seeded_locations(client: AsyncClient) -> None:
    await _register(client, "content-locations@example.com")

    response = await client.get("/api/content/locations")

    assert response.status_code == 200
    location_ids = {location["id"] for location in response.json()}
    assert {"ashfen_tavern_kitchen", "ashfen_east_fields"} <= location_ids


async def test_list_npcs_returns_seeded_npcs(client: AsyncClient) -> None:
    await _register(client, "content-npcs@example.com")

    response = await client.get("/api/content/npcs")

    assert response.status_code == 200
    npc_ids = {npc["id"] for npc in response.json()}
    assert {"mira_veyl", "osric_pike"} <= npc_ids


async def test_list_factions_returns_seeded_factions(client: AsyncClient) -> None:
    await _register(client, "content-factions@example.com")

    response = await client.get("/api/content/factions")

    assert response.status_code == 200
    faction_ids = {faction["id"] for faction in response.json()}
    assert {"ashfen_village_council", "moss_court"} <= faction_ids


async def test_list_origins_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/content/origins")

    assert response.status_code == 401


async def test_list_items_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/content/items")

    assert response.status_code == 401


async def test_list_locations_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/content/locations")

    assert response.status_code == 401


async def test_list_npcs_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/content/npcs")

    assert response.status_code == 401


async def test_list_factions_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/content/factions")

    assert response.status_code == 401
