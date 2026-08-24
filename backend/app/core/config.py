from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Mirrors google.genai.types.HarmBlockThreshold's practical values (excludes
# the UNSPECIFIED sentinel, which isn't meant to be set explicitly).
HarmBlockThresholdName = Literal[
    "BLOCK_NONE",
    "BLOCK_ONLY_HIGH",
    "BLOCK_MEDIUM_AND_ABOVE",
    "BLOCK_LOW_AND_ABOVE",
    "OFF",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "production"] = "development"
    database_url: str = "sqlite+aiosqlite:///./data/game.db"
    llm_provider: Literal["mock", "gemini"] = "mock"
    gemini_api_key: str = ""
    # gemini-2.5-flash-lite (research.md's original pin) is no longer
    # available to new API keys as of Task 47's canary test (2026-08-24) -
    # Google's own 404 response for it names gemini-3.5-flash-lite as the
    # replacement. See implementation-log.md Task 47 for the live-tested
    # findings behind this default.
    gemini_model: str = "gemini-3.5-flash-lite"
    # Starting-point safety thresholds for "dangerous but not graphic gore"
    # fantasy content (source doc's stated tone) - env-overridable so Task
    # 47's canary pass can tune them against real transcripts without a code
    # change. Threshold names match google.genai.types.HarmBlockThreshold.
    gemini_safety_dangerous_content: HarmBlockThresholdName = "BLOCK_ONLY_HIGH"
    gemini_safety_harassment: HarmBlockThresholdName = "BLOCK_ONLY_HIGH"
    gemini_safety_sexually_explicit: HarmBlockThresholdName = "BLOCK_MEDIUM_AND_ABOVE"
    # Default assumes the app runs with cwd=backend/ (e.g. `uv run uvicorn ...`
    # from that directory). Docker sets this to the mounted content path
    # (e.g. /app/content) instead.
    content_dir: str = "../content"
    # Source doc §7: proposed-action quantities must be "positive and within
    # configured bounds". No specific number is specified anywhere upstream -
    # provisional default, same status as Task 19's rate-limit thresholds.
    max_item_quantity: int = 99
    # Source doc §5/§7: game_state_json.recent_context is a bounded rolling
    # window of the most recent messages, kept alongside the full
    # story_messages history so prompt assembly (Task 42) can read it
    # without an extra query. No specific window size is specified upstream -
    # provisional default (5 player/narrator exchanges).
    recent_context_window: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
