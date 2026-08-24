FROM python:3.13-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Dependency-only layer first, so `docker build` can reuse the cached layer
# when only application code (not pyproject.toml/uv.lock) changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .
RUN uv sync --locked

# Production stage: only the built venv + app code cross the boundary - no
# uv binary, build cache, or apt lists. docker-compose.dev.yml instead
# builds against the `builder` stage above (still has uv + a writable venv
# for its own `uv sync && uv run --reload` command), so dev is unaffected.
FROM python:3.13-slim

WORKDIR /app

# Non-root: the app never needs root privileges at runtime.
RUN groupadd --system app \
    && useradd --system --gid app --no-create-home --shell /usr/sbin/nologin app

COPY --from=builder --chown=app:app /app /app

USER app

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
