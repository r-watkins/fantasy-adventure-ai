import json
from pathlib import Path

import pytest

from app.game.content_loader import load_content
from app.game.game_state import GameState
from app.llm.mock_provider import MockNarrativeProvider
from app.llm.provider import NarrativeProvider
from app.llm.schemas import NarrativeTurnRequest
from app.services.save_service import build_starting_game_state

pytestmark = pytest.mark.anyio

REPO_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"


def _request_at_turn(origin_id: str, turn_number: int, player_message: str) -> NarrativeTurnRequest:
    content = load_content(REPO_CONTENT_DIR)
    origin = next(o for o in content.origins.origins if o.id == origin_id)
    state = GameState.model_validate(build_starting_game_state(origin, "Avery"))
    state = state.model_copy(update={"turn_number": turn_number})
    return NarrativeTurnRequest(game_state=state, content=content, player_message=player_message)


def test_mock_provider_satisfies_protocol() -> None:
    assert isinstance(MockNarrativeProvider(), NarrativeProvider)


async def test_mock_provider_is_deterministic() -> None:
    provider = MockNarrativeProvider()
    request = _request_at_turn("tavern_cook", 2, "I inspect the ashes by the back door.")

    first = await provider.generate_turn(request)
    second = await provider.generate_turn(request)

    assert first == second


async def test_mock_provider_echoes_player_message_on_first_turn() -> None:
    provider = MockNarrativeProvider()
    request = _request_at_turn("tavern_cook", 0, "I inspect the ashes by the back door.")

    result = await provider.generate_turn(request)

    assert "I inspect the ashes by the back door." in result.narrative


async def test_mock_provider_cycles_narrative_beats_across_turns() -> None:
    provider = MockNarrativeProvider()
    narratives = []
    for turn_number in range(6):
        request = _request_at_turn("tavern_cook", turn_number, "I look around.")
        result = await provider.generate_turn(request)
        narratives.append(result.narrative)

    assert narratives[0] == narratives[3]
    assert narratives[1] == narratives[4]
    assert narratives[2] == narratives[5]
    assert len({narratives[0], narratives[1], narratives[2]}) == 3


async def test_mock_provider_grants_an_unheld_item_on_first_turn() -> None:
    provider = MockNarrativeProvider()
    request = _request_at_turn("tavern_cook", 0, "I look around.")
    held_item_ids = {entry.item_id for entry in request.game_state.inventory}

    result = await provider.generate_turn(request)

    assert len(result.proposed_actions) == 1
    action = result.proposed_actions[0]
    assert action.action_type == "add_item"
    payload = json.loads(action.payload)
    assert payload["item_id"] not in held_item_ids
    assert payload["quantity"] == 1


async def test_mock_provider_proposes_no_actions_after_first_turn() -> None:
    provider = MockNarrativeProvider()
    request = _request_at_turn("wheat_farmer", 1, "I keep walking.")

    result = await provider.generate_turn(request)

    assert result.proposed_actions == []
