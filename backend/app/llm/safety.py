from google.genai import types

from app.core.config import Settings


def build_safety_settings(settings: Settings) -> list[types.SafetySetting]:
    return [
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold=settings.gemini_safety_dangerous_content,
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold=settings.gemini_safety_harassment,
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold=settings.gemini_safety_sexually_explicit,
        ),
    ]
