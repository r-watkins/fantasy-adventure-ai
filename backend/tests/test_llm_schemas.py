from pathlib import Path

import pytest
from pydantic import ValidationError

from app.game.content_loader import load_content
from app.game.game_state import GameState
from app.llm.provider import NarrativeProvider
from app.llm.schemas import NarrativeTurnRequest, ProposedAction, TurnResult
from app.services.save_service import build_starting_game_state

REPO_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"

# The source design doc's §7 structured response example, verbatim.
DESIGN_DOC_TURN_RESULT = {
    "narrative": "Mira's gaze fixes on the wax seal. 'That mark should not be here,' she says.",
    "summary_update": (
        "Avery found an imperial wax seal in the tavern ashes; "
        "Mira recognized it and became more concerned."
    ),
    "proposed_actions": [
        {
            "type": "set_character_memory",
            "character_id": "mira_veyl",
            "memory": "Avery discovered an imperial wax seal in the tavern ashes.",
        },
        {
            "type": "set_world_flag",
            "flag": "imperial_seal_found",
            "value": True,
        },
    ],
}


def _as_flat_actions(design_doc_actions: list[dict]) -> list[dict]:
    # design.md's decision: flat {action_type, payload} shape, not the source
    # doc's inline-fields-per-type shape - re-flatten the doc's example into
    # what this schema actually accepts.
    flattened = []
    for action in design_doc_actions:
        action_type = action["type"]
        payload = {k: v for k, v in action.items() if k != "type"}
        flattened.append({"action_type": action_type, "payload": payload})
    return flattened


def test_turn_result_validates_flattened_design_doc_example() -> None:
    payload = {
        **DESIGN_DOC_TURN_RESULT,
        "proposed_actions": _as_flat_actions(DESIGN_DOC_TURN_RESULT["proposed_actions"]),
    }

    result = TurnResult.model_validate(payload)

    assert result.narrative.startswith("Mira's gaze")
    assert len(result.proposed_actions) == 2
    assert result.proposed_actions[0].action_type == "set_character_memory"
    assert result.proposed_actions[0].payload["character_id"] == "mira_veyl"
    assert result.proposed_actions[1].action_type == "set_world_flag"
    assert result.proposed_actions[1].payload["value"] is True


def test_turn_result_defaults_to_no_actions() -> None:
    result = TurnResult.model_validate(
        {"narrative": "The room is quiet.", "summary_update": "Nothing new happened."}
    )

    assert result.proposed_actions == []


def test_proposed_action_rejects_unknown_action_type() -> None:
    with pytest.raises(ValidationError):
        ProposedAction.model_validate({"action_type": "delete_save", "payload": {}})


@pytest.mark.parametrize(
    "action_type",
    [
        "add_item",
        "remove_item",
        "equip_item",
        "unequip_item",
        "set_world_flag",
        "set_character_memory",
        "set_character_relationship",
        "set_character_status",
        "update_quest",
        "move_player",
    ],
)
def test_proposed_action_accepts_each_allowed_type(action_type: str) -> None:
    action = ProposedAction.model_validate({"action_type": action_type, "payload": {"a": 1}})
    assert action.action_type == action_type


def test_narrative_turn_request_builds_from_real_content_and_state() -> None:
    content = load_content(REPO_CONTENT_DIR)
    origin = next(o for o in content.origins.origins if o.id == "tavern_cook")
    state = GameState.model_validate(build_starting_game_state(origin, "Avery"))

    request = NarrativeTurnRequest(
        game_state=state,
        content=content,
        player_message="I inspect the ashes by the back door.",
    )

    assert request.player_message == "I inspect the ashes by the back door."
    assert request.game_state.player.origin_id == "tavern_cook"


def test_conforming_provider_satisfies_protocol() -> None:
    class ConformingProvider:
        async def generate_turn(self, request: NarrativeTurnRequest) -> TurnResult:
            return TurnResult(narrative="...", summary_update="...")

    assert isinstance(ConformingProvider(), NarrativeProvider)


def test_non_conforming_provider_does_not_satisfy_protocol() -> None:
    class NotAProvider:
        pass

    assert not isinstance(NotAProvider(), NarrativeProvider)
