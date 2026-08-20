from typing import Any, Literal

from pydantic import BaseModel

from app.game.content_schemas import GameContent
from app.game.game_state import GameState

# Flat action_type + payload shape, not a Pydantic discriminated union -
# google-genai's response_schema currently errors on discriminated unions
# (SDK issue #652). Discrimination/validation happens in backend code
# (app/services, Task 32) regardless, per the "server validates" principle.
ActionType = Literal[
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
]


class ProposedAction(BaseModel):
    action_type: ActionType
    payload: dict[str, Any] = {}


class TurnResult(BaseModel):
    narrative: str
    summary_update: str
    proposed_actions: list[ProposedAction] = []


class NarrativeTurnRequest(BaseModel):
    game_state: GameState
    content: GameContent
    player_message: str
