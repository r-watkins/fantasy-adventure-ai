# Contributing

Thanks for your interest in Fantasy AI Adventure. This project is early in development; the notes below will grow as the codebase does.

## Local development

Full setup instructions live in [README.md](README.md) once Phase 1 of the initial implementation checklist lands. In short: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`, with `LLM_PROVIDER=mock` so no external API key is required to run the app.

## Code style

- **Backend** (`backend/`): Python, formatted and linted with [Ruff](https://docs.astral.sh/ruff/). Run `uv run ruff check .` before committing.
- **Frontend** (`frontend/`): TypeScript, linted with ESLint. Run `npm run lint` before committing.

## Tests

- **Backend**: `pytest` (async tests via the `anyio` pytest plugin). Run `uv run pytest`.
- **Frontend**: `vitest` for components, `playwright` for end-to-end flows.

CI runs both suites on every push and pull request to `main`.

## Pull requests

Keep changes small and focused — one logical change per PR, with tests for new behavior. Describe *why* a change is needed, not just what changed.

## Reporting issues

Open a GitHub issue with steps to reproduce, expected vs. actual behavior, and relevant logs (redact anything sensitive — never paste API keys, session tokens, or `.env` contents).
