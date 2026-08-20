from pathlib import Path

import pytest
from pydantic import ValidationError

from app.game.content_loader import load_content
from app.game.game_state import GameState
from app.services.save_service import build_starting_game_state

REPO_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"

# The source design doc's §5 example payload, verbatim.
DESIGN_DOC_EXAMPLE = {
    "schema_version": 1,
    "turn_number": 4,
    "player": {
        "name": "Avery",
        "origin_id": "tavern_cook",
        "origin_label": "Tavern Cook",
        "location_id": "ashfen_tavern_kitchen",
        "traits": ["resourceful", "observant"],
    },
    "inventory": [
        {"item_id": "iron_cook_knife", "quantity": 1, "equipped": True},
        {"item_id": "ember_charm", "quantity": 1, "equipped": False},
    ],
    "characters": {
        "mira_veyl": {
            "relationship": "cautious ally",
            "status": "waiting in the common room",
            "memory": "The player kept Mira's secret about the missing ledger.",
        }
    },
    "world_flags": {
        "tavern_fire_extinguished": True,
        "east_gate_open": False,
    },
    "quests": [
        {
            "quest_id": "missing_ledger",
            "status": "active",
            "objective": "Find who stole the innkeeper's ledger.",
        }
    ],
    "story_summary": (
        "Avery, a tavern cook in Ashfen, stopped a kitchen fire and earned Mira's "
        "guarded trust. A clue in the ashes points toward the east gate."
    ),
    "recent_context": [
        {"role": "player", "content": "I inspect the ashes by the back door."},
        {
            "role": "narrator",
            "content": "Beneath the soot, your knife catches on a silver wax seal...",
        },
    ],
}


def test_game_state_validates_design_doc_example() -> None:
    state = GameState.model_validate(DESIGN_DOC_EXAMPLE)

    assert state.schema_version == 1
    assert state.turn_number == 4
    assert state.player.name == "Avery"
    assert state.inventory[0].item_id == "iron_cook_knife"
    assert state.characters["mira_veyl"].relationship == "cautious ally"
    assert state.world_flags["tavern_fire_extinguished"] is True
    assert state.quests[0].quest_id == "missing_ledger"
    assert state.recent_context[0].role == "player"


def test_game_state_round_trips_through_dump() -> None:
    state = GameState.model_validate(DESIGN_DOC_EXAMPLE)

    assert GameState.model_validate(state.model_dump()) == state


@pytest.mark.parametrize("origin_id", ["tavern_cook", "wheat_farmer"])
def test_game_state_validates_real_starting_state(origin_id: str) -> None:
    content = load_content(REPO_CONTENT_DIR)
    origin = next(o for o in content.origins.origins if o.id == origin_id)

    starting_state = build_starting_game_state(origin, "Traveler")

    state = GameState.model_validate(starting_state)
    assert state.player.origin_id == origin_id
    assert state.turn_number == 0
    assert state.recent_context[0].content == origin.opening_hook


def test_game_state_requires_player() -> None:
    payload = {k: v for k, v in DESIGN_DOC_EXAMPLE.items() if k != "player"}

    with pytest.raises(ValidationError):
        GameState.model_validate(payload)


def test_game_state_defaults_are_empty() -> None:
    state = GameState.model_validate(
        {
            "player": {
                "name": "Avery",
                "origin_id": "tavern_cook",
                "origin_label": "Tavern Cook",
                "location_id": "ashfen_tavern_kitchen",
            }
        }
    )

    assert state.schema_version == 1
    assert state.turn_number == 0
    assert state.inventory == []
    assert state.characters == {}
    assert state.world_flags == {}
    assert state.quests == []
    assert state.story_summary == ""
    assert state.recent_context == []
