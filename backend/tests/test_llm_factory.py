import pytest

from app.core.config import Settings
from app.llm.factory import NarrativeProviderConfigError, build_narrative_provider
from app.llm.gemini_provider import GeminiNarrativeProvider
from app.llm.mock_provider import MockNarrativeProvider


def test_default_settings_build_the_mock_provider() -> None:
    provider = build_narrative_provider(Settings())

    assert isinstance(provider, MockNarrativeProvider)


def test_llm_provider_gemini_builds_the_gemini_provider_with_settings_wired_through() -> None:
    settings = Settings(
        llm_provider="gemini", gemini_api_key="fake-key", gemini_model="gemini-2.5-flash-lite"
    )

    provider = build_narrative_provider(settings)

    assert isinstance(provider, GeminiNarrativeProvider)
    assert provider._model == "gemini-2.5-flash-lite"


def test_llm_provider_gemini_without_an_api_key_fails_fast() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key="")

    with pytest.raises(NarrativeProviderConfigError):
        build_narrative_provider(settings)
