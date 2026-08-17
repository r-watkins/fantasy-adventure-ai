from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: database engine/sessionmaker wiring (Task 4) and content
    # validation (Task 6) attach here once those pieces exist.
    yield
    # Shutdown: engine disposal attaches here once Task 4 adds the engine.


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Fantasy AI Adventure API", lifespan=lifespan)
    app.state.settings = settings
    return app


app = create_app()
