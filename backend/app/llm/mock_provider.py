from app.llm.schemas import NarrativeTurnRequest, ProposedAction, TurnResult

# Deterministic canned narrative beats, cycled by the current turn number - no
# randomness, so the same (game_state, content, player_message) always
# produces the same TurnResult. Lets local dev/CI/E2E exercise the full
# gameplay loop without GEMINI_API_KEY.
_SCENARIO_BEATS: tuple[str, ...] = (
    "You act: {player_message} The scene shifts in response.",
    "Ashfen holds its breath, waiting to see what happens next.",
    "The moment settles. Something nearby seems to notice you.",
)


class MockNarrativeProvider:
    async def generate_turn(self, request: NarrativeTurnRequest) -> TurnResult:
        state = request.game_state
        turn_index = state.turn_number

        beat = _SCENARIO_BEATS[turn_index % len(_SCENARIO_BEATS)]
        narrative = beat.format(player_message=request.player_message.strip())

        proposed_actions: list[ProposedAction] = []
        if turn_index == 0:
            held_item_ids = {entry.item_id for entry in state.inventory}
            new_item = next(
                (item for item in request.content.items.items if item.id not in held_item_ids),
                None,
            )
            if new_item is not None:
                proposed_actions.append(
                    ProposedAction(
                        action_type="add_item",
                        payload={"item_id": new_item.id, "quantity": 1},
                    )
                )

        return TurnResult(
            narrative=narrative,
            summary_update=f"Turn {turn_index + 1}: {narrative}",
            proposed_actions=proposed_actions,
        )
