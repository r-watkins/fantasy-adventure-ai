import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _register(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/auth/register", json={"email": email, "password": "correct horse battery"}
    )
    assert response.status_code == 201


async def test_create_save_builds_starting_state_from_origin(client: AsyncClient) -> None:
    await _register(client, "saver@example.com")

    response = await client.post(
        "/api/saves", json={"origin_id": "tavern_cook", "character_name": "Avery"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["origin_id"] == "tavern_cook"
    assert body["name"] == "Tavern Cook"
    assert body["archived_at"] is None


async def test_create_save_rejects_unknown_origin(client: AsyncClient) -> None:
    await _register(client, "badorigin@example.com")

    response = await client.post("/api/saves", json={"origin_id": "not-a-real-origin"})

    assert response.status_code == 422


async def test_create_save_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/api/saves", json={"origin_id": "tavern_cook"})

    assert response.status_code == 401


async def test_get_save_detail_includes_opening_narrator_message(client: AsyncClient) -> None:
    await _register(client, "detail@example.com")
    create_response = await client.post(
        "/api/saves", json={"origin_id": "tavern_cook", "character_name": "Avery"}
    )
    save_id = create_response.json()["id"]

    response = await client.get(f"/api/saves/{save_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["game_state_json"]["player"]["name"] == "Avery"
    assert body["game_state_json"]["player"]["location_id"]
    assert len(body["messages"]) == 1
    assert body["messages"][0]["role"] == "narrator"
    assert body["messages"][0]["turn_number"] == 0


async def test_list_saves_excludes_archived(client: AsyncClient) -> None:
    await _register(client, "lister@example.com")
    create_response = await client.post("/api/saves", json={"origin_id": "wheat_farmer"})
    save_id = create_response.json()["id"]

    await client.post("/api/saves", json={"origin_id": "tavern_cook"})

    patch_response = await client.patch(f"/api/saves/{save_id}", json={"archived": True})
    assert patch_response.status_code == 200
    assert patch_response.json()["archived_at"] is not None

    list_response = await client.get("/api/saves")
    assert list_response.status_code == 200
    ids = [save["id"] for save in list_response.json()]
    assert save_id not in ids
    assert len(ids) == 1


async def test_patch_save_renames_slot(client: AsyncClient) -> None:
    await _register(client, "renamer@example.com")
    create_response = await client.post("/api/saves", json={"origin_id": "tavern_cook"})
    save_id = create_response.json()["id"]

    response = await client.patch(f"/api/saves/{save_id}", json={"name": "My Kitchen Run"})

    assert response.status_code == 200
    assert response.json()["name"] == "My Kitchen Run"


async def test_save_endpoints_reject_another_users_save_id(client: AsyncClient) -> None:
    await _register(client, "owner@example.com")
    create_response = await client.post("/api/saves", json={"origin_id": "tavern_cook"})
    save_id = create_response.json()["id"]
    await client.post("/api/auth/logout")

    await _register(client, "intruder@example.com")

    get_response = await client.get(f"/api/saves/{save_id}")
    assert get_response.status_code == 404

    patch_response = await client.patch(f"/api/saves/{save_id}", json={"name": "Hijacked"})
    assert patch_response.status_code == 404

    list_response = await client.get("/api/saves")
    assert list_response.json() == []
