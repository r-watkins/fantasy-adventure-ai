import httpx
from google import genai
from google.genai import errors, types

from app.llm.prompt import assemble_turn_prompt
from app.llm.schemas import NarrativeTurnRequest, TurnResult

# Google's guidance: allow enough headroom for a real generation call under
# load (each retry attempt below gets this long before the SDK gives up on
# it and re-raises).
_REQUEST_TIMEOUT_MS = 120_000

# httpx exceptions the SDK itself treats as transient/retryable internally;
# if they still survive every retry attempt, they propagate here unwrapped.
_TRANSIENT_NETWORK_ERRORS = (httpx.TimeoutException, httpx.ConnectError)


class GeminiTurnGenerationError(Exception):
    """Raised when Gemini could not produce a usable TurnResult - covers a
    parsed=None response as well as any API/network failure that survived
    the SDK's own retry-on-429/5xx behavior. The message is always a
    sanitized, generic description (no raw provider response text, no
    keys) - safe to log or otherwise surface without redaction.
    """


class GeminiNarrativeProvider:
    def __init__(
        self, api_key: str, model: str, safety_settings: list[types.SafetySetting]
    ) -> None:
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=_REQUEST_TIMEOUT_MS,
                # Without an explicit retry_options, google-genai does NOT
                # retry at all (verified against the installed SDK:
                # retry_args() returns stop_after_attempt(1) when
                # retry_options is None) - this opts into its documented
                # defaults instead: 5 attempts with exponential backoff, on
                # 408/429/500/502/503/504 only, so 400/403/404 still fail
                # fast without any extra configuration here.
                retry_options=types.HttpRetryOptions(),
            ),
        )
        self._model = model
        self._safety_settings = safety_settings

    async def generate_turn(self, request: NarrativeTurnRequest) -> TurnResult:
        prompt = assemble_turn_prompt(request)
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt.contents,
                config=types.GenerateContentConfig(
                    system_instruction=prompt.system_instruction,
                    response_mime_type="application/json",
                    response_schema=TurnResult,
                    safety_settings=self._safety_settings,
                ),
            )
        except errors.APIError as exc:
            raise GeminiTurnGenerationError(
                f"Gemini API request failed (status {exc.code} {exc.status})"
            ) from exc
        except _TRANSIENT_NETWORK_ERRORS as exc:
            raise GeminiTurnGenerationError(
                "Gemini request failed due to a network timeout or connection error"
            ) from exc

        if response.parsed is None:
            raise GeminiTurnGenerationError(
                "Gemini response contained no parsable structured output"
            )
        return response.parsed
