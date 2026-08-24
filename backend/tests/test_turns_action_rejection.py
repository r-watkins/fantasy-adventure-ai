"""Endpoint-level coverage for the turn endpoint's proposed-action rejection
paths, per source doc §13's acceptance list: invalid item ID, negative
quantity, unauthorized consume action, malformed JSON/action. Task 32's own
test suite already exercises the validation service exhaustively at the unit
level - this file proves the same rejections hold end-to-end through
POST /api/saves/{save_id}/turns, each with zero state mutation asserted.
"""

import json
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


def _payload(**kwargs: object) -> str:
    return json.dumps(kwargs)


def _provider_returning(*actions: ProposedAction):
    class _FixedProvider:
        async def generate_turn(self, request: NarrativeTurnRequest) -> TurnResult:
            return TurnResult(narrative="...", summary_update="...", proposed_actions=list(actions))

    return _FixedProvider()


async def _run_rejected_turn_scenario(
    migrated_db_url: str, provider, *, origin_id: str = "tavern_cook"
) -> None:
    app = create_app()
    app.state.settings = Settings(database_url=migrated_db_url, content_dir=str(REPO_CONTENT_DIR))
    app.dependency_overrides[get_narrative_provider] = lambda: provider

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            register_response = await client.post(
                "/api/auth/register",
                json={"email": "rejecter@example.com", "password": "correct horse battery"},
            )
            assert register_response.status_code == 201

            create_response = await client.post(
                "/api/saves", json={"origin_id": origin_id, "character_name": "Avery"}
            )
            assert create_response.status_code == 201
            save_id = create_response.json()["id"]

            before = await client.get(f"/api/saves/{save_id}")
            before_body = before.json()

            response = await client.post(
                f"/api/saves/{save_id}/turns", json={"message": "I try something risky."}
            )
            assert response.status_code == 502
            assert "detail" in response.json()

            after = await client.get(f"/api/saves/{save_id}")
            after_body = after.json()

            assert after_body["game_state_json"] == before_body["game_state_json"]
            assert after_body["messages"] == before_body["messages"]


async def test_turn_rejects_invalid_item_id(migrated_db_url: str) -> None:
    provider = _provider_returning(
        ProposedAction(
            action_type="add_item", payload=_payload(item_id="not_a_real_item", quantity=1)
        )
    )
    await _run_rejected_turn_scenario(migrated_db_url, provider)


async def test_turn_rejects_negative_quantity(migrated_db_url: str) -> None:
    provider = _provider_returning(
        ProposedAction(action_type="add_item", payload=_payload(item_id="ember_charm", quantity=-1))
    )
    await _run_rejected_turn_scenario(migrated_db_url, provider)


async def test_turn_rejects_unauthorized_consume_action(migrated_db_url: str) -> None:
    # tavern_cook's starting inventory doesn't include ember_charm - removing
    # an item the player never owns is exactly the "unauthorized consume"
    # case source doc §13 calls out.
    provider = _provider_returning(
        ProposedAction(
            action_type="remove_item", payload=_payload(item_id="ember_charm", quantity=1)
        )
    )
    await _run_rejected_turn_scenario(migrated_db_url, provider)


async def test_turn_rejects_unauthorized_equip_action(migrated_db_url: str) -> None:
    provider = _provider_returning(
        ProposedAction(action_type="equip_item", payload=_payload(item_id="ember_charm"))
    )
    await _run_rejected_turn_scenario(migrated_db_url, provider)


async def test_turn_rejects_malformed_action_missing_required_field(migrated_db_url: str) -> None:
    # "malformed" at this layer: the action parses fine as a ProposedAction
    # (action_type is a valid Literal) but its payload is missing a field
    # the applier requires - item_id here.
    provider = _provider_returning(
        ProposedAction(action_type="add_item", payload=_payload(quantity=1))
    )
    await _run_rejected_turn_scenario(migrated_db_url, provider)


async def test_turn_rejects_action_with_payload_that_is_not_valid_json(
    migrated_db_url: str,
) -> None:
    # Task 47's live canary test found the model sometimes fills payload
    # with a bare string instead of JSON (e.g. "Iron Cook Knife") - this is
    # the direct endpoint-level regression test for that exact failure mode.
    provider = _provider_returning(
        ProposedAction(action_type="equip_item", payload="Iron Cook Knife")
    )
    await _run_rejected_turn_scenario(migrated_db_url, provider)


async def test_turn_rejects_when_one_of_several_actions_is_invalid(migrated_db_url: str) -> None:
    # A batch of actions where only the last is bad must still roll back the
    # earlier, individually-valid ones - the all-or-nothing guarantee.
    provider = _provider_returning(
        ProposedAction(action_type="add_item", payload=_payload(item_id="ember_charm", quantity=1)),
        ProposedAction(
            action_type="set_world_flag", payload=_payload(flag="east_gate_open", value=True)
        ),
        ProposedAction(
            action_type="move_player", payload=_payload(location_id="nonexistent_location")
        ),
    )
    await _run_rejected_turn_scenario(migrated_db_url, provider)
