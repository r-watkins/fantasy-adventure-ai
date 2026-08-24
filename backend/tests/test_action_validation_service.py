import json
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.game.content_loader import load_content
from app.game.game_state import GameState
from app.llm.schemas import ProposedAction
from app.services.action_validation_service import (
    ActionValidationError,
    validate_and_apply_actions,
)
from app.services.save_service import build_starting_game_state

REPO_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"


@pytest.fixture
def content():
    return load_content(REPO_CONTENT_DIR)


@pytest.fixture
def tavern_cook_state(content):
    origin = next(o for o in content.origins.origins if o.id == "tavern_cook")
    return GameState.model_validate(build_starting_game_state(origin, "Avery"))


def _action(action_type: str, **payload) -> ProposedAction:
    return ProposedAction(action_type=action_type, payload=json.dumps(payload))


# --- add_item -----------------------------------------------------------


def test_add_item_creates_new_inventory_entry(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state, content, [_action("add_item", item_id="ember_charm", quantity=1)]
    )

    entry = next(e for e in result.inventory if e.item_id == "ember_charm")
    assert entry.quantity == 1
    assert entry.equipped is False


def test_add_item_increments_existing_quantity(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state,
        content,
        [_action("add_item", item_id="iron_cook_knife", quantity=2)],
    )

    entry = next(e for e in result.inventory if e.item_id == "iron_cook_knife")
    assert entry.quantity == 3  # starting inventory already has 1


def test_add_item_rejects_unknown_item_id(content, tavern_cook_state):
    with pytest.raises(ActionValidationError, match="Unknown item_id"):
        validate_and_apply_actions(
            tavern_cook_state, content, [_action("add_item", item_id="nonexistent", quantity=1)]
        )


@pytest.mark.parametrize("quantity", [0, -1])
def test_add_item_rejects_non_positive_quantity(content, tavern_cook_state, quantity):
    with pytest.raises(ActionValidationError, match="positive"):
        validate_and_apply_actions(
            tavern_cook_state,
            content,
            [_action("add_item", item_id="ember_charm", quantity=quantity)],
        )


def test_add_item_rejects_quantity_over_configured_bound(content, tavern_cook_state):
    over_limit = get_settings().max_item_quantity + 1
    with pytest.raises(ActionValidationError, match="exceeds the maximum"):
        validate_and_apply_actions(
            tavern_cook_state,
            content,
            [_action("add_item", item_id="ember_charm", quantity=over_limit)],
        )


def test_add_item_rejects_non_integer_quantity(content, tavern_cook_state):
    with pytest.raises(ActionValidationError, match="must be an integer"):
        validate_and_apply_actions(
            tavern_cook_state,
            content,
            [_action("add_item", item_id="ember_charm", quantity="a lot")],
        )


# --- remove_item ----------------------------------------------------------


def test_remove_item_decrements_quantity(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state,
        content,
        [
            _action("add_item", item_id="ember_charm", quantity=2),
            _action("remove_item", item_id="ember_charm", quantity=1),
        ],
    )

    entry = next(e for e in result.inventory if e.item_id == "ember_charm")
    assert entry.quantity == 1


def test_remove_item_drops_entry_at_zero(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state,
        content,
        [_action("remove_item", item_id="iron_cook_knife", quantity=1)],
    )

    assert not any(e.item_id == "iron_cook_knife" for e in result.inventory)


def test_remove_item_rejects_unowned_item(content, tavern_cook_state):
    with pytest.raises(ActionValidationError, match="does not own enough"):
        validate_and_apply_actions(
            tavern_cook_state,
            content,
            [_action("remove_item", item_id="ember_charm", quantity=1)],
        )


def test_remove_item_rejects_removing_more_than_owned(content, tavern_cook_state):
    with pytest.raises(ActionValidationError, match="does not own enough"):
        validate_and_apply_actions(
            tavern_cook_state,
            content,
            [_action("remove_item", item_id="iron_cook_knife", quantity=5)],
        )


# --- equip_item / unequip_item --------------------------------------------


def test_equip_item_requires_ownership(content, tavern_cook_state):
    with pytest.raises(ActionValidationError, match="does not own"):
        validate_and_apply_actions(
            tavern_cook_state, content, [_action("equip_item", item_id="ember_charm")]
        )


def test_equip_item_succeeds_when_owned(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state, content, [_action("equip_item", item_id="iron_cook_knife")]
    )

    entry = next(e for e in result.inventory if e.item_id == "iron_cook_knife")
    assert entry.equipped is True


def test_unequip_item_requires_ownership(content, tavern_cook_state):
    with pytest.raises(ActionValidationError, match="does not own"):
        validate_and_apply_actions(
            tavern_cook_state, content, [_action("unequip_item", item_id="ember_charm")]
        )


def test_equip_then_unequip_in_same_turn(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state,
        content,
        [
            _action("equip_item", item_id="iron_cook_knife"),
            _action("unequip_item", item_id="iron_cook_knife"),
        ],
    )

    entry = next(e for e in result.inventory if e.item_id == "iron_cook_knife")
    assert entry.equipped is False


def test_add_then_equip_in_same_turn_sees_just_added_item(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state,
        content,
        [
            _action("add_item", item_id="ember_charm", quantity=1),
            _action("equip_item", item_id="ember_charm"),
        ],
    )

    entry = next(e for e in result.inventory if e.item_id == "ember_charm")
    assert entry.equipped is True


# --- set_world_flag ---------------------------------------------------------


def test_set_world_flag_sets_boolean(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state, content, [_action("set_world_flag", flag="east_gate_open", value=True)]
    )

    assert result.world_flags["east_gate_open"] is True


def test_set_world_flag_rejects_non_boolean_value(content, tavern_cook_state):
    with pytest.raises(ActionValidationError, match="must be a boolean"):
        validate_and_apply_actions(
            tavern_cook_state,
            content,
            [_action("set_world_flag", flag="east_gate_open", value="yes")],
        )


# --- character actions -------------------------------------------------------


def test_set_character_memory_creates_character_with_defaults(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state,
        content,
        [_action("set_character_memory", character_id="mira_veyl", memory="Found the seal.")],
    )

    character = result.characters["mira_veyl"]
    assert character.memory == "Found the seal."
    assert character.relationship == "unknown"
    assert character.status == "unknown"


def test_set_character_relationship_then_status_preserves_memory(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state,
        content,
        [
            _action("set_character_memory", character_id="mira_veyl", memory="Found the seal."),
            _action("set_character_relationship", character_id="mira_veyl", relationship="ally"),
            _action("set_character_status", character_id="mira_veyl", status="waiting"),
        ],
    )

    character = result.characters["mira_veyl"]
    assert character.memory == "Found the seal."
    assert character.relationship == "ally"
    assert character.status == "waiting"


@pytest.mark.parametrize(
    "action_type", ["set_character_memory", "set_character_relationship", "set_character_status"]
)
def test_character_actions_reject_unknown_npc(content, tavern_cook_state, action_type):
    field = {
        "set_character_memory": "memory",
        "set_character_relationship": "relationship",
        "set_character_status": "status",
    }[action_type]
    with pytest.raises(ActionValidationError, match="Unknown character_id"):
        validate_and_apply_actions(
            tavern_cook_state,
            content,
            [_action(action_type, character_id="nonexistent_npc", **{field: "x"})],
        )


# --- update_quest -------------------------------------------------------------


def test_update_quest_starts_new_quest_with_objective(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state,
        content,
        [
            _action(
                "update_quest",
                quest_id="missing_ledger",
                status="active",
                objective="Find the ledger.",
            )
        ],
    )

    quest = next(q for q in result.quests if q.quest_id == "missing_ledger")
    assert quest.status == "active"
    assert quest.objective == "Find the ledger."


def test_update_quest_without_objective_requires_existing_quest(content, tavern_cook_state):
    with pytest.raises(ActionValidationError, match="requires an 'objective'"):
        validate_and_apply_actions(
            tavern_cook_state,
            content,
            [_action("update_quest", quest_id="missing_ledger", status="active")],
        )


def test_update_quest_updates_status_of_existing_quest(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state,
        content,
        [
            _action(
                "update_quest",
                quest_id="missing_ledger",
                status="active",
                objective="Find the ledger.",
            ),
            _action("update_quest", quest_id="missing_ledger", status="completed"),
        ],
    )

    quest = next(q for q in result.quests if q.quest_id == "missing_ledger")
    assert quest.status == "completed"
    assert quest.objective == "Find the ledger."


def test_update_quest_rejects_unknown_status(content, tavern_cook_state):
    with pytest.raises(ActionValidationError, match="status"):
        validate_and_apply_actions(
            tavern_cook_state,
            content,
            [_action("update_quest", quest_id="missing_ledger", status="on_hold", objective="Go.")],
        )


# --- move_player ---------------------------------------------------------------


def test_move_player_updates_location(content, tavern_cook_state):
    result = validate_and_apply_actions(
        tavern_cook_state, content, [_action("move_player", location_id="ashfen_tavern")]
    )

    assert result.player.location_id == "ashfen_tavern"


def test_move_player_rejects_unknown_location(content, tavern_cook_state):
    with pytest.raises(ActionValidationError, match="Unknown location_id"):
        validate_and_apply_actions(
            tavern_cook_state, content, [_action("move_player", location_id="nonexistent")]
        )


# --- payload JSON parsing -------------------------------------------------------
# payload is a JSON-encoded string, not a dict (Task 47 finding: a dict-typed
# field renders as additionalProperties in the response schema, rejected by
# the Gemini Developer API) - these cover the json.loads() step directly.


def test_payload_that_is_not_valid_json_is_rejected(content, tavern_cook_state):
    action = ProposedAction(action_type="equip_item", payload="Iron Cook Knife")

    with pytest.raises(ActionValidationError, match="not valid JSON"):
        validate_and_apply_actions(tavern_cook_state, content, [action])


def test_payload_that_is_a_json_array_not_object_is_rejected(content, tavern_cook_state):
    action = ProposedAction(action_type="equip_item", payload="[1, 2, 3]")

    with pytest.raises(ActionValidationError, match="must be a JSON object"):
        validate_and_apply_actions(tavern_cook_state, content, [action])


# --- allowlist / zero-mutation guarantees ---------------------------------------


def test_disallowed_action_type_is_rejected(content, tavern_cook_state):
    action = _action("add_item", item_id="ember_charm", quantity=1)
    action.action_type = "delete_save"  # bypass ProposedAction's own Literal check

    with pytest.raises(ActionValidationError, match="not allowed"):
        validate_and_apply_actions(tavern_cook_state, content, [action])


def test_failed_action_leaves_original_state_untouched(content, tavern_cook_state):
    original_inventory_length = len(tavern_cook_state.inventory)

    with pytest.raises(ActionValidationError):
        validate_and_apply_actions(
            tavern_cook_state,
            content,
            [
                _action("add_item", item_id="ember_charm", quantity=1),
                _action("add_item", item_id="nonexistent", quantity=1),
            ],
        )

    assert len(tavern_cook_state.inventory) == original_inventory_length
    assert not any(e.item_id == "ember_charm" for e in tavern_cook_state.inventory)


def test_validate_and_apply_actions_does_not_mutate_input_state(content, tavern_cook_state):
    validate_and_apply_actions(
        tavern_cook_state, content, [_action("add_item", item_id="ember_charm", quantity=1)]
    )

    assert not any(e.item_id == "ember_charm" for e in tavern_cook_state.inventory)


def test_empty_action_list_returns_equivalent_state(content, tavern_cook_state):
    result = validate_and_apply_actions(tavern_cook_state, content, [])

    assert result == tavern_cook_state
    assert result is not tavern_cook_state
