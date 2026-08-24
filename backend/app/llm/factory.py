from app.core.config import Settings
from app.llm.gemini_provider import GeminiNarrativeProvider
from app.llm.mock_provider import MockNarrativeProvider
from app.llm.provider import NarrativeProvider
from app.llm.safety import build_safety_settings


class NarrativeProviderConfigError(RuntimeError):
    """Raised when settings.llm_provider is misconfigured, e.g. 'gemini'
    selected with no GEMINI_API_KEY set.
    """


def build_narrative_provider(settings: Settings) -> NarrativeProvider:
    if settings.llm_provider == "mock":
        return MockNarrativeProvider()

    if not settings.gemini_api_key:
        raise NarrativeProviderConfigError("LLM_PROVIDER=gemini requires GEMINI_API_KEY to be set")

    return GeminiNarrativeProvider(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        safety_settings=build_safety_settings(settings),
    )
