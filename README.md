# Fantasy AI Adventure

[![Demo](https://img.shields.io/badge/Demo-Live%20App-brightgreen?style=for-the-badge)](https://my-open-works.net/fantasy-adventure-ai/)

An open-source, self-hostable, browser-based fantasy text adventure. Players interact with an AI narrator through a chat interface that sets scenes, portrays NPCs, reacts to free-form player actions, and develops an ongoing adventure in the style of a tabletop fantasy role-playing session.

The narrator is an LLM assistant; game state (accounts, saves, inventory, world flags, quests) is always authoritative server-side data, never something the model owns. The stack runs locally with a single Docker Compose command and is deployable to a single low-traffic AWS Lightsail instance, with no managed cloud services required.

## Status

Feature-complete for v1: accounts and saves, the full game loop against a real Gemini narrator (with an offline mock-provider fallback for local dev), and a documented production deployment path to a single AWS Lightsail instance. See [deploy/lightsail/README.md](deploy/lightsail/README.md) to deploy.

## Local development

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/) with Compose v2 (`docker compose`, not the standalone `docker-compose`).

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

This starts two services with hot reload:

- **Frontend** (Vite dev server) — http://localhost:5173
- **Backend** (FastAPI, `uvicorn --reload`) — http://localhost:8000, health check at http://localhost:8000/api/health

The frontend proxies `/api/*` requests to the backend itself (see `frontend/vite.config.ts`), so the browser only ever talks to `http://localhost:5173` — no CORS configuration needed in dev.

By default `LLM_PROVIDER=mock`, so the app runs fully offline with no external API key required.

SQLite data persists in a named Docker volume (`sqlite_data`) across restarts. To reset it entirely: `docker compose down -v`.

A seed command that creates a test user and sample save for local development is a nice-to-have, not yet built.

### Running without Docker

The frontend and backend can also run directly on the host if you have a current Node.js LTS and [uv](https://docs.astral.sh/uv/) installed:

```bash
# Backend
cd backend
uv run uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Without Docker, the frontend's `/api` proxy falls back to `http://localhost:8000` automatically.

### Tests and linting

```bash
# Backend
cd backend
uv run pytest
uv run ruff check .

# Frontend
cd frontend
npm run test
npm run lint
npx tsc -b

# Frontend end-to-end (Playwright - spins up its own isolated backend
# and dev server, doesn't need Docker or a running dev stack)
npm run test:e2e
```

### Environment variables

All variables live in `.env` (copied from `.env.example`, gitignored). Docker Compose overrides `DATABASE_URL` and `CONTENT_DIR` to container-internal paths regardless of what's in `.env` — see `docker-compose.yml`.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/game.db` | SQLAlchemy async connection string. Ignored inside Docker (see above). |
| `ENVIRONMENT` | `development` | `development` \| `production`. |
| `LLM_PROVIDER` | `mock` | `mock` (deterministic, offline) \| `gemini` (real API calls, requires `GEMINI_API_KEY`). |
| `GEMINI_API_KEY` | *(empty)* | Required only when `LLM_PROVIDER=gemini`. |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Gemini model ID. |
| `GEMINI_SAFETY_DANGEROUS_CONTENT` | `BLOCK_ONLY_HIGH` | Safety threshold for dangerous-content generation. One of `BLOCK_NONE` \| `BLOCK_ONLY_HIGH` \| `BLOCK_MEDIUM_AND_ABOVE` \| `BLOCK_LOW_AND_ABOVE` \| `OFF`. |
| `GEMINI_SAFETY_HARASSMENT` | `BLOCK_ONLY_HIGH` | Safety threshold for harassment content. Same value set as above. |
| `GEMINI_SAFETY_SEXUALLY_EXPLICIT` | `BLOCK_MEDIUM_AND_ABOVE` | Safety threshold for sexually explicit content. Same value set as above. |
| `SESSION_COOKIE_PATH` | `/` | Path attribute of the session cookie. Keep `/` for local dev; production sets `/fantasy-adventure-ai` so the cookie isn't sent to other apps sharing the domain. The domain itself (`SITE_ADDRESS`) is configured for the edge proxy in `deploy/edge/.env`, not here. |
| `CONTENT_DIR` | `../content` | Path to the world/items/NPCs/origins YAML content. Overridden to a container-internal path by Docker Compose regardless of `.env` (see above). |
| `MAX_ITEM_QUANTITY` | `99` | Upper bound the server enforces on any LLM-proposed item quantity (`add_item`/`remove_item`). Provisional - no specific number is mandated anywhere upstream. |
| `RECENT_CONTEXT_WINDOW` | `10` | Number of recent player/narrator messages kept in the rolling context sent to the LLM each turn. Larger values improve narrative continuity at the cost of more tokens per Gemini call. |

## Production deployment

In production the app is served under a subdirectory, `https://<domain>/fantasy-adventure-ai/`, so the same domain can host a landing page and other small static prototypes at `/prototypes/<id>/`. Two Docker Compose projects cooperate over a shared `edge` Docker network:

- **App** (this directory's `docker-compose.yml`, `--profile production`): `api` plus a `web` container (Caddy) that serves the frontend built with the `/fantasy-adventure-ai/` base path and proxies `/fantasy-adventure-ai/api/*` to the backend. It publishes no ports.
- **Edge** (`deploy/edge/`): the shared Caddy that owns ports 80/443 and automatic HTTPS, serves the landing page and the prototypes folder, and forwards `/fantasy-adventure-ai*` to the app.

```bash
docker network create edge                                  # once per host
docker compose --profile production up -d --build           # the app
cd deploy/edge && cp .env.example .env && docker compose up -d   # the edge (set SITE_ADDRESS first)
```

The `--profile production` flag matters — it's what starts the Caddy `web` service alongside `api`. Without it, only `api` starts, which is what local dev overlays use instead (`docker-compose.dev.yml` never runs Caddy, and local dev stays at `http://localhost:5173/` with no subdirectory).

The subdirectory is a build-time setting (`VITE_BASE_PATH` in `docker-compose.yml`) that must match `deploy/Caddyfile`, `deploy/edge/Caddyfile` and `SESSION_COOKIE_PATH`; a mismatch shows up as a blank page. This assumes `.env` is already configured with a real `GEMINI_API_KEY`, `ENVIRONMENT=production` and `SESSION_COOKIE_PATH=/fantasy-adventure-ai`. For the complete walkthrough — provisioning a fresh AWS Lightsail instance, DNS, firewall rules, the edge proxy, adding prototypes, migrating an existing root-level deployment, nightly backups, and testing backup restoration — see **[deploy/lightsail/README.md](deploy/lightsail/README.md)**.

## Stack

| Component | Technology |
|---|---|
| Web client | React + Vite + TypeScript, shadcn/ui (Tailwind CSS v4 + Base UI) |
| API | Python + FastAPI |
| Database | SQLite (WAL mode) |
| LLM provider | Pluggable adapter; Gemini (`gemini-3.5-flash-lite`) as the first implementation, with a deterministic mock provider for offline development |
| Reverse proxy | Caddy |
| Deployment | Docker Compose (local dev and single-instance production) |

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
