from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_narrative_provider
from app.core.config import Settings
from app.llm.schemas import NarrativeTurnRequest, ProposedAction, TurnResult
from app.main import create_app

pytestmark = pytest.mark.anyio

REPO_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"


async def _register_and_create_save(client: AsyncClient, email: str, origin_id: str) -> str:
    register_response = await client.post(
        "/api/auth/register", json={"email": email, "password": "correct horse battery"}
    )
    assert register_response.status_code == 201

    create_response = await client.post(
        "/api/saves", json={"origin_id": origin_id, "character_name": "Avery"}
    )
    assert create_response.status_code == 201
    return create_response.json()["id"]


async def test_submit_turn_returns_contract_shape(client: AsyncClient) -> None:
    save_id = await _register_and_create_save(client, "turner@example.com", "tavern_cook")

    response = await client.post(
        f"/api/saves/{save_id}/turns",
        json={"message": "I inspect the ashes by the back door."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["player_message"]["role"] == "player"
    assert body["player_message"]["content"] == "I inspect the ashes by the back door."
    assert body["narrator_message"]["role"] == "narrator"
    assert body["player_message"]["id"] != body["narrator_message"]["id"]
    assert body["turn_number"] == 1
    assert body["game_state"]["turn_number"] == 1
    assert body["game_state"]["player"]["name"] == "Avery"


async def test_submit_turn_persists_state_and_messages(client: AsyncClient) -> None:
    save_id = await _register_and_create_save(client, "persist@example.com", "tavern_cook")

    await client.post(f"/api/saves/{save_id}/turns", json={"message": "I look around."})

    detail_response = await client.get(f"/api/saves/{save_id}")
    body = detail_response.json()
    assert body["game_state_json"]["turn_number"] == 1
    # Opening narrator message (turn 0) + this turn's player/narrator pair.
    assert len(body["messages"]) == 3
    assert [m["role"] for m in body["messages"]] == ["narrator", "player", "narrator"]


async def test_first_turn_grants_item_via_mock_provider(client: AsyncClient) -> None:
    save_id = await _register_and_create_save(client, "granted@example.com", "tavern_cook")

    response = await client.post(f"/api/saves/{save_id}/turns", json={"message": "I look around."})

    inventory = response.json()["game_state"]["inventory"]
    item_ids = {entry["item_id"] for entry in inventory}
    assert "iron_cook_knife" in item_ids  # starting item, untouched
    assert len(item_ids) == 2  # mock provider granted exactly one more


async def test_second_turn_increments_and_does_not_regrant(client: AsyncClient) -> None:
    save_id = await _register_and_create_save(client, "secondturn@example.com", "wheat_farmer")

    await client.post(f"/api/saves/{save_id}/turns", json={"message": "First."})
    second_response = await client.post(
        f"/api/saves/{save_id}/turns", json={"message": "Second."}
    )

    body = second_response.json()
    assert body["turn_number"] == 2
    item_ids = [entry["item_id"] for entry in body["game_state"]["inventory"]]
    assert len(item_ids) == len(set(item_ids))  # no duplicate/re-granted entries


async def test_submit_turn_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/api/saves/some-id/turns", json={"message": "Hello?"})

    assert response.status_code == 401


async def test_submit_turn_rejects_another_users_save(client: AsyncClient) -> None:
    save_id = await _register_and_create_save(client, "turnowner@example.com", "tavern_cook")
    await client.post("/api/auth/logout")

    await client.post(
        "/api/auth/register",
        json={"email": "turnintruder@example.com", "password": "correct horse battery"},
    )

    response = await client.post(f"/api/saves/{save_id}/turns", json={"message": "Hello?"})

    assert response.status_code == 404


async def test_submit_turn_rejects_empty_message(client: AsyncClient) -> None:
    save_id = await _register_and_create_save(client, "emptymsg@example.com", "tavern_cook")

    response = await client.post(f"/api/saves/{save_id}/turns", json={"message": ""})

    assert response.status_code == 422


async def test_submit_turn_rejects_nonexistent_save(client: AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "nosave@example.com", "password": "correct horse battery"},
    )

    response = await client.post("/api/saves/does-not-exist/turns", json={"message": "Hello?"})

    assert response.status_code == 404


class _RejectingProvider:
    async def generate_turn(self, request: NarrativeTurnRequest) -> TurnResult:
        return TurnResult(
            narrative="...",
            summary_update="...",
            proposed_actions=[
                ProposedAction(action_type="add_item", payload={"item_id": "nonexistent"})
            ],
        )


async def test_submit_turn_rejects_invalid_action_with_zero_mutation(
    migrated_db_url: str,
) -> None:
    app = create_app()
    app.state.settings = Settings(database_url=migrated_db_url, content_dir=str(REPO_CONTENT_DIR))
    app.dependency_overrides[get_narrative_provider] = lambda: _RejectingProvider()

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            save_id = await _register_and_create_save(
                client, "rejected@example.com", "tavern_cook"
            )

            response = await client.post(
                f"/api/saves/{save_id}/turns", json={"message": "I try something impossible."}
            )
            assert response.status_code == 502

            detail_response = await client.get(f"/api/saves/{save_id}")
            body = detail_response.json()
            assert body["game_state_json"]["turn_number"] == 0
            assert len(body["messages"]) == 1
