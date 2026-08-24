from google import genai
from google.genai import types

from app.llm.prompt import assemble_turn_prompt
from app.llm.schemas import NarrativeTurnRequest, TurnResult


class GeminiTurnGenerationError(Exception):
    """Raised when Gemini's response could not be parsed into a TurnResult."""


class GeminiNarrativeProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate_turn(self, request: NarrativeTurnRequest) -> TurnResult:
        prompt = assemble_turn_prompt(request)
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt.contents,
            config=types.GenerateContentConfig(
                system_instruction=prompt.system_instruction,
                response_mime_type="application/json",
                response_schema=TurnResult,
            ),
        )
        if response.parsed is None:
            raise GeminiTurnGenerationError(
                "Gemini response contained no parsable structured output"
            )
        return response.parsed
