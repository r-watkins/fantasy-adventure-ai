from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.me import router as me_router
from app.core.config import get_settings
from app.db.session import create_engine, create_session_factory
from app.game.content_loader import load_content


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = app.state.settings
    engine = create_engine(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    # Fail fast: an invalid content directory should crash startup rather
    # than run with broken/missing world content.
    app.state.content = load_content(Path(settings.content_dir))

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Fantasy AI Adventure API", lifespan=lifespan)
    app.state.settings = settings
    app.include_router(health_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(me_router, prefix="/api")
    return app


app = create_app()
