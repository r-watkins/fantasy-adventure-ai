from collections.abc import Callable
from typing import Any

from app.core.config import get_settings
from app.game.content_schemas import GameContent
from app.game.game_state import CharacterState, GameState, InventoryEntry, Quest
from app.llm.schemas import ProposedAction

_ALLOWED_QUEST_STATUSES = {"active", "completed", "failed"}


class ActionValidationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _require_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ActionValidationError(f"'{key}' must be a non-empty string")
    return value


def _require_bool(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ActionValidationError(f"'{key}' must be a boolean")
    return value


def _require_positive_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ActionValidationError(f"'{key}' must be an integer")
    if value <= 0:
        raise ActionValidationError(f"'{key}' must be positive")
    max_quantity = get_settings().max_item_quantity
    if value > max_quantity:
        raise ActionValidationError(f"'{key}' exceeds the maximum allowed ({max_quantity})")
    return value


def _find_inventory_entry(state: GameState, item_id: str) -> InventoryEntry | None:
    return next((entry for entry in state.inventory if entry.item_id == item_id), None)


def _get_or_create_character(state: GameState, character_id: str) -> CharacterState:
    character = state.characters.get(character_id)
    if character is None:
        character = CharacterState(relationship="unknown", status="unknown", memory="")
        state.characters[character_id] = character
    return character


def _apply_add_item(state: GameState, content: GameContent, payload: dict[str, Any]) -> None:
    item_id = _require_str(payload, "item_id")
    quantity = _require_positive_int(payload, "quantity")
    if item_id not in content.item_ids:
        raise ActionValidationError(f"Unknown item_id '{item_id}'")

    existing = _find_inventory_entry(state, item_id)
    if existing is not None:
        existing.quantity += quantity
    else:
        state.inventory.append(InventoryEntry(item_id=item_id, quantity=quantity, equipped=False))


def _apply_remove_item(state: GameState, content: GameContent, payload: dict[str, Any]) -> None:
    item_id = _require_str(payload, "item_id")
    quantity = _require_positive_int(payload, "quantity")
    if item_id not in content.item_ids:
        raise ActionValidationError(f"Unknown item_id '{item_id}'")

    existing = _find_inventory_entry(state, item_id)
    if existing is None or existing.quantity < quantity:
        raise ActionValidationError(f"Player does not own enough of '{item_id}' to remove")

    existing.quantity -= quantity
    if existing.quantity == 0:
        state.inventory.remove(existing)


def _apply_equip_item(state: GameState, content: GameContent, payload: dict[str, Any]) -> None:
    item_id = _require_str(payload, "item_id")
    if item_id not in content.item_ids:
        raise ActionValidationError(f"Unknown item_id '{item_id}'")

    existing = _find_inventory_entry(state, item_id)
    if existing is None:
        raise ActionValidationError(f"Player does not own '{item_id}' to equip")
    existing.equipped = True


def _apply_unequip_item(state: GameState, content: GameContent, payload: dict[str, Any]) -> None:
    item_id = _require_str(payload, "item_id")
    if item_id not in content.item_ids:
        raise ActionValidationError(f"Unknown item_id '{item_id}'")

    existing = _find_inventory_entry(state, item_id)
    if existing is None:
        raise ActionValidationError(f"Player does not own '{item_id}' to unequip")
    existing.equipped = False


def _apply_set_world_flag(state: GameState, content: GameContent, payload: dict[str, Any]) -> None:
    flag = _require_str(payload, "flag")
    value = _require_bool(payload, "value")
    state.world_flags[flag] = value


def _apply_set_character_memory(
    state: GameState, content: GameContent, payload: dict[str, Any]
) -> None:
    character_id = _require_str(payload, "character_id")
    memory = _require_str(payload, "memory")
    if character_id not in content.npc_ids:
        raise ActionValidationError(f"Unknown character_id '{character_id}'")
    _get_or_create_character(state, character_id).memory = memory


def _apply_set_character_relationship(
    state: GameState, content: GameContent, payload: dict[str, Any]
) -> None:
    character_id = _require_str(payload, "character_id")
    relationship = _require_str(payload, "relationship")
    if character_id not in content.npc_ids:
        raise ActionValidationError(f"Unknown character_id '{character_id}'")
    _get_or_create_character(state, character_id).relationship = relationship


def _apply_set_character_status(
    state: GameState, content: GameContent, payload: dict[str, Any]
) -> None:
    character_id = _require_str(payload, "character_id")
    status = _require_str(payload, "status")
    if character_id not in content.npc_ids:
        raise ActionValidationError(f"Unknown character_id '{character_id}'")
    _get_or_create_character(state, character_id).status = status


def _apply_update_quest(state: GameState, content: GameContent, payload: dict[str, Any]) -> None:
    quest_id = _require_str(payload, "quest_id")
    status = _require_str(payload, "status")
    if status not in _ALLOWED_QUEST_STATUSES:
        raise ActionValidationError(f"'status' must be one of {sorted(_ALLOWED_QUEST_STATUSES)}")

    objective = payload.get("objective")
    if objective is not None and not isinstance(objective, str):
        raise ActionValidationError("'objective' must be a string")

    existing = next((q for q in state.quests if q.quest_id == quest_id), None)
    if existing is not None:
        existing.status = status
        if objective:
            existing.objective = objective
        return

    if not objective:
        raise ActionValidationError(
            f"Unknown quest_id '{quest_id}' requires an 'objective' to start it"
        )
    state.quests.append(Quest(quest_id=quest_id, status=status, objective=objective))


def _apply_move_player(state: GameState, content: GameContent, payload: dict[str, Any]) -> None:
    location_id = _require_str(payload, "location_id")
    if location_id not in content.location_ids:
        raise ActionValidationError(f"Unknown location_id '{location_id}'")
    state.player.location_id = location_id


_ACTION_APPLIERS: dict[str, Callable[[GameState, GameContent, dict[str, Any]], None]] = {
    "add_item": _apply_add_item,
    "remove_item": _apply_remove_item,
    "equip_item": _apply_equip_item,
    "unequip_item": _apply_unequip_item,
    "set_world_flag": _apply_set_world_flag,
    "set_character_memory": _apply_set_character_memory,
    "set_character_relationship": _apply_set_character_relationship,
    "set_character_status": _apply_set_character_status,
    "update_quest": _apply_update_quest,
    "move_player": _apply_move_player,
}


def validate_and_apply_actions(
    state: GameState, content: GameContent, actions: list[ProposedAction]
) -> GameState:
    """Validate every proposed action against a working copy of `state` and
    apply it. Raises ActionValidationError on the first invalid action,
    leaving the caller's original `state` untouched either way - the caller
    should only persist the returned value, never `state` itself, and only
    once every action here has succeeded.
    """
    working_state = state.model_copy(deep=True)
    for action in actions:
        applier = _ACTION_APPLIERS.get(action.action_type)
        if applier is None:
            raise ActionValidationError(f"Action type '{action.action_type}' is not allowed")
        applier(working_state, content, action.payload)
    return working_state
