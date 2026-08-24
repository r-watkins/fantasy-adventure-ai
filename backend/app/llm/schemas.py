from typing import Literal

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
    # JSON-encoded object, not a dict[str, Any] - found at Task 47's canary
    # test: a dict-typed field renders as a JSON schema with
    # additionalProperties, which the Gemini Developer API (api-key auth,
    # used here) rejects client-side for response_schema. Parsed with
    # json.loads() in action_validation_service.py; malformed JSON is
    # treated as a rejected/malformed action, same as any other bad payload.
    payload: str = "{}"


class TurnResult(BaseModel):
    narrative: str
    summary_update: str
    proposed_actions: list[ProposedAction] = []


class NarrativeTurnRequest(BaseModel):
    game_state: GameState
    content: GameContent
    player_message: str
