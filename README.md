# Fantasy AI Adventure

An open-source, self-hostable, browser-based fantasy text adventure. Players interact with an AI narrator through a chat interface that sets scenes, portrays NPCs, reacts to free-form player actions, and develops an ongoing adventure in the style of a tabletop fantasy role-playing session.

The narrator is an LLM assistant; game state (accounts, saves, inventory, world flags, quests) is always authoritative server-side data, never something the model owns. The stack runs locally with a single Docker Compose command and is deployable to a single low-traffic AWS Lightsail instance, with no managed cloud services required.

## Status

Early development — following an implementation checklist phase by phase. Local development instructions land here once Phase 1 of that checklist is complete.

## Stack

| Component | Technology |
|---|---|
| Web client | React + Vite + TypeScript, shadcn/ui (Tailwind CSS v4 + Base UI) |
| API | Python + FastAPI |
| Database | SQLite (WAL mode) |
| LLM provider | Pluggable adapter; Gemini (`gemini-2.5-flash-lite`) as the first implementation, with a deterministic mock provider for offline development |
| Reverse proxy | Caddy |
| Deployment | Docker Compose (local dev and single-instance production) |

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
