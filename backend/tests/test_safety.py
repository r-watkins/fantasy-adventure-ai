from app.core.config import Settings
from app.llm.safety import build_safety_settings


def test_default_safety_settings_match_the_design_starting_point() -> None:
    settings = build_safety_settings(Settings())

    by_category = {setting.category: setting.threshold for setting in settings}
    assert by_category["HARM_CATEGORY_DANGEROUS_CONTENT"] == "BLOCK_ONLY_HIGH"
    assert by_category["HARM_CATEGORY_HARASSMENT"] == "BLOCK_ONLY_HIGH"
    assert by_category["HARM_CATEGORY_SEXUALLY_EXPLICIT"] == "BLOCK_MEDIUM_AND_ABOVE"


def test_safety_settings_are_overridable_via_settings() -> None:
    settings = Settings(
        gemini_safety_dangerous_content="BLOCK_NONE",
        gemini_safety_harassment="BLOCK_LOW_AND_ABOVE",
        gemini_safety_sexually_explicit="OFF",
    )

    by_category = {
        setting.category: setting.threshold for setting in build_safety_settings(settings)
    }

    assert by_category["HARM_CATEGORY_DANGEROUS_CONTENT"] == "BLOCK_NONE"
    assert by_category["HARM_CATEGORY_HARASSMENT"] == "BLOCK_LOW_AND_ABOVE"
    assert by_category["HARM_CATEGORY_SEXUALLY_EXPLICIT"] == "OFF"
