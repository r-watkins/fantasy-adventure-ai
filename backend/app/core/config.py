from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "production"] = "development"
    database_url: str = "sqlite+aiosqlite:///./data/game.db"
    llm_provider: Literal["mock", "gemini"] = "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    # Default assumes the app runs with cwd=backend/ (e.g. `uv run uvicorn ...`
    # from that directory). Docker sets this to the mounted content path
    # (e.g. /app/content) instead.
    content_dir: str = "../content"
    # Source doc §7: proposed-action quantities must be "positive and within
    # configured bounds". No specific number is specified anywhere upstream -
    # provisional default, same status as Task 19's rate-limit thresholds.
    max_item_quantity: int = 99


@lru_cache
def get_settings() -> Settings:
    return Settings()
