from google import genai
from google.genai import types

from app.llm.schemas import NarrativeTurnRequest, TurnResult


class GeminiTurnGenerationError(Exception):
    """Raised when Gemini's response could not be parsed into a TurnResult."""


class GeminiNarrativeProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate_turn(self, request: NarrativeTurnRequest) -> TurnResult:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=_build_turn_prompt(request),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TurnResult,
            ),
        )
        if response.parsed is None:
            raise GeminiTurnGenerationError(
                "Gemini response contained no parsable structured output"
            )
        return response.parsed


def _build_turn_prompt(request: NarrativeTurnRequest) -> str:
    # Minimal placeholder prompt - Task 42 replaces this with the real prompt
    # assembly function (system_instruction from narrator_system.md +
    # delimited world/state/summary/recent-context blocks). Needed now only
    # so this provider has something concrete to send.
    state_json = request.game_state.model_dump_json()
    return f"Current game state (JSON):\n{state_json}\n\nPlayer action:\n{request.player_message}"
