from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.auth import router as auth_router
from app.api.content import router as content_router
from app.api.health import router as health_router
from app.api.me import router as me_router
from app.api.saves import router as saves_router
from app.api.turns import router as turns_router
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import create_engine, create_session_factory
from app.game.content_loader import load_content
from app.llm.factory import build_narrative_provider


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = app.state.settings
    engine = create_engine(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    # Fail fast: an invalid content directory should crash startup rather
    # than run with broken/missing world content.
    app.state.content = load_content(Path(settings.content_dir))

    # Fail fast: LLM_PROVIDER=gemini with no GEMINI_API_KEY should crash
    # startup, not the first turn a player submits.
    app.state.narrative_provider = build_narrative_provider(settings)

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Fantasy AI Adventure API", lifespan=lifespan)
    app.state.settings = settings
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    app.include_router(health_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(me_router, prefix="/api")
    app.include_router(saves_router, prefix="/api")
    app.include_router(turns_router, prefix="/api")
    app.include_router(content_router, prefix="/api")
    return app


app = create_app()
