# Deploying to AWS Lightsail

A complete, from-scratch guide to running Fantasy AI Adventure on a single
AWS Lightsail instance: no managed database, no load balancer, no other
AWS services required.

## How it is hosted

The app is served under a subdirectory of your domain,
`https://<domain>/fantasy-adventure-ai/`, so the same domain and instance
can also host a landing page (`/`) and other small static prototypes
(`/prototypes/<id>/`). Two Docker Compose projects share the instance and
talk over an external Docker network named `edge`:

| Project | Where | Owns |
|---|---|---|
| App | `/opt/fantasy-ai-adventure` (repo root, `--profile production`) | `api` (FastAPI) and `web` (Caddy serving the frontend built for the `/fantasy-adventure-ai/` prefix). Publishes **no** host ports. |
| Edge | `/opt/fantasy-ai-adventure/deploy/edge` | The shared Caddy on ports 80/443: HTTPS certificates, the landing page, `/prototypes/*`, and routing `/fantasy-adventure-ai*` to the app. |

Keeping them separate means adding or updating a prototype never restarts
the app, and redeploying the app never drops the prototypes.

## Prerequisites

- An AWS account.
- A domain name you control, with the ability to add DNS records (via
  Lightsail's own DNS zone, or your existing registrar/DNS provider).
- A [Gemini API key](https://aistudio.google.com/) if you intend to run
  with the real LLM provider (`LLM_PROVIDER=gemini`).

## 1. Create the instance

1. In the [Lightsail console](https://lightsail.aws.amazon.com/), choose
   **Create instance**.
2. Platform: **Linux/Unix**. Blueprint: **OS Only → Ubuntu 24.04 LTS**.
3. Instance plan: the **2 GB RAM / 2 vCPU / 60 GB SSD** bundle (currently
   $12/mo). The 0.5 GB/1 GB bundles are not recommended - Docker Engine
   overhead plus two containers (FastAPI + Caddy) plus SQLite plus
   occasional LLM-call latency/memory spikes comfortably fits 2 GB, but is
   OOM-risky on the smaller tiers unless you never build images on-host.
4. Name the instance (e.g. `fantasy-ai-adventure`) and create it.

## 2. Attach a static IP

Instance IPs are not static by default - if the instance restarts, a
dynamic IP can change, breaking DNS.

1. Lightsail console → **Networking** tab → **Create static IP**.
2. Attach it to the instance you just created.
3. Note the static IP address - you'll point DNS at it next.

## 3. Point DNS at the instance

Add an **A record** for the domain (or subdomain) you want to serve the
site from, pointing at the static IP from step 2. If the instance is
dual-stack (IPv4 + IPv6, the Lightsail default), also add an **AAAA record**
pointing at the instance's public IPv6 address (shown on the Networking
tab) - otherwise IPv6-only visitors can't reach it. This can be done either
through Lightsail's own DNS zone (**Networking → DNS zones**) or through
your existing registrar/DNS provider - whichever already manages the
domain.

DNS propagation can take anywhere from a few minutes to 48 hours. Confirm
it's resolved (`dig +short your-domain.example.com` or
`nslookup your-domain.example.com`) before continuing - Caddy's automatic
HTTPS (step 6) will fail to obtain a certificate if the domain doesn't yet
resolve to this instance.

## 4. Configure the firewall

Lightsail console → your instance → **Networking** tab → **IPv4 Firewall**
(and **IPv6 Firewall**, if the instance is dual-stack - the same rules
apply). Only these three rules should be present:

| Application | Protocol | Port |
|---|---|---|
| SSH | TCP | 22 |
| HTTP | TCP | 80 |
| HTTPS | TCP | 443 |

Remove any other default rules. Port 80 is required even though the site
serves HTTPS - Caddy uses it for the ACME HTTP-01 challenge during
certificate issuance/renewal and to redirect plain HTTP to HTTPS.

## 5. Bootstrap the instance

SSH into the instance (Lightsail's browser-based SSH client works, or your
own SSH client with the downloaded key pair):

```bash
curl -fsSL https://raw.githubusercontent.com/r-watkins/fantasy-adventure-ai/main/deploy/lightsail/bootstrap.sh | bash
```

This installs Docker Engine + the Compose plugin, grants your user
passwordless `docker` access, clones the repo to
`/opt/fantasy-ai-adventure`, and creates a starter `.env`. It's safe to
re-run if interrupted.

If this was your first time being added to the `docker` group, log out and
back in (or run `newgrp docker`) before continuing.

## 6. Configure and start the stack

### 6a. The app

```bash
cd /opt/fantasy-ai-adventure
nano .env   # or your editor of choice
```

At minimum, set:

- `GEMINI_API_KEY` - your real key (leave `LLM_PROVIDER=mock` instead if
  you want to run without one, at least initially).
- `ENVIRONMENT=production`.
- `SESSION_COOKIE_PATH=/fantasy-adventure-ai` - scopes the login cookie to
  the app so it isn't sent to other prototypes on the same domain.

The domain name is **not** set here any more - it belongs to the edge
(step 6b).

Then create the shared network (once per host) and start the app:

```bash
docker network create edge
docker compose --profile production up -d --build
```

Note the `--profile production` flag - it's required. The `web` (Caddy)
service is gated behind that profile so that local development, which
never runs Caddy, doesn't accidentally build and start it too.

`entrypoint.sh` runs `alembic upgrade head` automatically (as the
unprivileged `app` user) before the API starts, so no manual migration step
is needed - look for `Running upgrade ... -> ..., baseline schema` in the
`api` logs (`docker compose logs -f api web`).

### 6b. The edge

```bash
sudo mkdir -p /opt/prototypes && sudo chown "$USER": /opt/prototypes
cd /opt/fantasy-ai-adventure/deploy/edge
cp .env.example .env
nano .env   # SITE_ADDRESS=your real domain, PROTOTYPES_DIR=/opt/prototypes
docker compose up -d
docker compose logs -f edge
```

`SITE_ADDRESS` is what Caddy uses to request the Let's Encrypt
certificate - it must already resolve to this instance (step 3). To serve
several names, comma-separate them (`example.com, www.example.com`). Look
for `certificate obtained successfully` in the edge logs; if it never
appears, double-check DNS has propagated and the firewall allows port 80.

At this point `https://<your-domain>/` shows the landing page and the app is
live at `https://<your-domain>/fantasy-adventure-ai/`.

If you ever need to run a one-off admin command against the database
directly (not part of normal deployment), use
`docker compose exec --user app api /app/.venv/bin/alembic <command>` -
`--user app` matters because `docker compose exec` defaults to root (the
image has no `USER` directive), and a root-run command would create
root-owned files the actual unprivileged process then can't write to.

## 7. Set up nightly backups

Install and enable the backup timer:

```bash
cd /opt/fantasy-ai-adventure
sudo cp deploy/systemd/fantasy-backup.service deploy/systemd/fantasy-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now fantasy-backup.timer
```

Verify it's scheduled:

```bash
systemctl list-timers fantasy-backup.timer
```

Backups run nightly at 03:00 (server local time), landing in
`/opt/fantasy-ai-adventure/backups/{daily,weekly}/` - 7 daily snapshots and
4 weekly snapshots are retained, older ones are pruned automatically. See
`deploy/lightsail/backup.sh` for the mechanics.

To test the timer without waiting for 03:00:

```bash
sudo systemctl start fantasy-backup.service
sudo journalctl -u fantasy-backup.service -n 20
```

## 8. Test backup restoration

**An untested backup isn't a backup.** Do this once after your first real
backup exists, and periodically thereafter. `/opt/fantasy-ai-adventure` is
the compose project's directory, so the image Docker Compose already built
in step 6 is tagged `fantasy-ai-adventure-api` (Compose derives the
project name from the directory basename) - both steps below reuse that
image directly rather than assuming any tooling is installed on the host.

```bash
cd /opt/fantasy-ai-adventure
BACKUP_FILE="$(ls -t backups/daily/*.db | head -1)"

# 1. Integrity check - confirms the snapshot isn't corrupt.
docker run --rm -v "$(pwd)/$BACKUP_FILE:/backup.db:ro" fantasy-ai-adventure-api \
  python3 -c "import sqlite3; print(sqlite3.connect('/backup.db').execute('PRAGMA integrity_check').fetchone())"
# Expect: ('ok',)

# 2. Throwaway app run - actually boot the app against the restored file,
#    proving it's not just structurally valid but genuinely usable. No
#    --user override needed: entrypoint.sh always chowns /data to the
#    unprivileged app user at container start, regardless of who owned the
#    files beforehand.
mkdir -p /tmp/restore-test
cp "$BACKUP_FILE" /tmp/restore-test/game.db
docker run --rm -d --name restore-test \
  -v /tmp/restore-test:/data \
  -v "$(pwd)/content:/app/content:ro" \
  -e DATABASE_URL="sqlite+aiosqlite:////data/game.db" \
  -e CONTENT_DIR=/app/content \
  -e LLM_PROVIDER=mock \
  -p 8001:8000 \
  fantasy-ai-adventure-api
```

With that running:

```bash
curl http://localhost:8001/api/health
# {"status":"ok"}

# Register a throwaway account and confirm it can read from the restored
# database - proves both write (registration) and read (listing saves)
# work against the restored file, without needing the original backed-up
# user's credentials.
curl -c /tmp/restore-cookies.txt -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"restore-check@example.com","password":"correct horse battery"}'
curl -b /tmp/restore-cookies.txt http://localhost:8001/api/saves
# []
```

Once confirmed, tear it down:

```bash
docker rm -f restore-test
rm -rf /tmp/restore-test /tmp/restore-cookies.txt
```

To actually restore a backup in place (disaster recovery, not just a
test) - stop the stack first so nothing is writing to the database while
you replace it:

```bash
cd /opt/fantasy-ai-adventure
BACKUP_FILE="$(ls -t backups/daily/*.db | head -1)"   # or pick a specific one

docker compose --profile production down
VOLUME_PATH="$(docker volume inspect fantasy-ai-adventure_sqlite_data --format '{{.Mountpoint}}')"
sudo cp "$BACKUP_FILE" "$VOLUME_PATH/game.db"
sudo rm -f "$VOLUME_PATH/game.db-wal" "$VOLUME_PATH/game.db-shm"   # stale WAL/SHM from the old file
docker compose --profile production up -d
```

`sudo` is required for the volume path - Docker-managed volumes live under
`/var/lib/docker/volumes/`, owned by root.

## Adding a prototype

Prototypes are static files served from `PROTOTYPES_DIR` (`/opt/prototypes`),
one folder per id, with no edge restart or config change:

```bash
# on your machine: build the prototype for its URL, e.g. with Vite
#   base: '/prototypes/my-idea/'   (or './' for relative asset paths)
scp -r dist/. ubuntu@<instance>:/opt/prototypes/my-idea/
```

It is then live at `https://<your-domain>/prototypes/my-idea/`. To list it
on the landing page, add an entry to `deploy/edge/landing/index.html` (see
the comment there) and `git pull` - the landing folder is mounted live, so no
restart is needed. Prototypes share the domain with the app, so only host
code you trust: a prototype's JavaScript runs on the same origin as the app.

## Migrating an existing deployment from the domain root

For an instance that already serves the app directly at `https://<domain>/`
(the layout before the subdirectory move). Plan for a few minutes of
downtime while ports 80/443 change owner and the edge obtains a new
certificate.

**Before you start**

- Note your current `SITE_ADDRESS`
  (`grep SITE_ADDRESS /opt/fantasy-ai-adventure/.env`) - it moves to the
  edge's `.env`. Leave it in the app's `.env` for now: it is what makes a
  rollback work.
- Check DNS: the A record points at the instance's static IP, and an AAAA
  record exists if you want IPv6 (step 3). Firewall rules for 80/443 should
  already be open for IPv4 and IPv6 (step 4).
- Never run `docker compose down -v` anywhere in this procedure - it would
  delete the database volume.

**Cutover**

```bash
cd /opt/fantasy-ai-adventure
git pull

# 1. App settings: scope the cookie to the subdirectory.
echo 'SESSION_COOKIE_PATH=/fantasy-adventure-ai' >> .env

# 2. Shared network and edge settings (same domain as before).
docker network create edge
sudo mkdir -p /opt/prototypes && sudo chown "$USER": /opt/prototypes
cp deploy/edge/.env.example deploy/edge/.env
nano deploy/edge/.env          # SITE_ADDRESS=<current domain>, PROTOTYPES_DIR=/opt/prototypes

# 3. Build the new app images while the old site is still serving.
docker compose --profile production build

# 4. Cutover (downtime starts): recreate the app - the new `web` publishes
#    no ports, which frees 80/443 - then start the edge.
docker compose --profile production up -d
(cd deploy/edge && docker compose up -d && docker compose logs -f edge)
```

Wait for `certificate obtained successfully`, then verify:

```bash
DOMAIN=<your-domain>
curl -sI https://$DOMAIN/ | head -1                                  # 200 (landing page)
curl -sI https://$DOMAIN/fantasy-adventure-ai | head -1              # 308 -> .../fantasy-adventure-ai/
curl -s  https://$DOMAIN/fantasy-adventure-ai/api/health             # {"status":"ok"}
curl -sI https://$DOMAIN/saves | grep -i location                    # -> /fantasy-adventure-ai/saves
```

Then open `https://<your-domain>/fantasy-adventure-ai/` in a browser and
log in. Existing logged-in users stay logged in (their old cookie is still
sent under the new path); it is replaced by a path-scoped cookie the next
time they log in or out.

**Cleaning up later**

- `/saves`, `/new-game`, `/game/*` and `/settings` at the domain root
  redirect to the app so old bookmarks keep working. Remove the `@legacy`
  block in `deploy/edge/Caddyfile` once they are no longer needed. The old
  root-level `/api/*` URLs are not redirected (they are no longer served).
- The code that deletes the old `Path=/` session cookie on login/logout
  (`clear_legacy_session_cookie` in `backend/app/core/security.py`) can be
  removed once the longest-lived legacy cookie (7 days) has expired.
- Once you're confident, remove the unused `SITE_ADDRESS` line from the
  app's `.env`.

**Rollback** (if something is wrong and you need the old layout back)

```bash
cd /opt/fantasy-ai-adventure/deploy/edge && docker compose down   # frees 80/443; no -v
cd /opt/fantasy-ai-adventure
git log --oneline -n 20          # find the last commit before the subdirectory change
git checkout <that-commit>
docker compose --profile production up -d --build
git checkout main                # afterwards, to return to the current branch
```

The old `web` reuses its original `caddy_data` volume, so its certificate
is still there. Users logged in under the new layout will simply need to
log in again.

## Updating the deployment

```bash
cd /opt/fantasy-ai-adventure
git pull
docker compose --profile production up -d --build          # the app
(cd deploy/edge && docker compose up -d)                   # the edge, if deploy/edge changed
```

Compose only recreates containers whose image or config actually changed,
so this is safe to run even when nothing changed. The edge and prototypes
keep serving while the app restarts (the app briefly returns 502 under
`/fantasy-adventure-ai/`).

## Troubleshooting

- **Caddy won't get a certificate**: confirm DNS resolves to the
  instance's static IP (`dig +short your-domain`), and that ports 80/443
  are open in the Lightsail firewall (step 4). The edge owns the
  certificate now: check `docker compose logs edge` in `deploy/edge` for the
  specific TLS error.
- **`network edge declared as external, but could not be found`**: run
  `docker network create edge` (step 6a).
- **Blank page at `/fantasy-adventure-ai/`**: the frontend's build-time base
  path doesn't match the Caddy prefix (a missing asset is answered with
  `index.html`, so it looks like a blank page rather than a 404). Check
  `VITE_BASE_PATH` in `docker-compose.yml` is `/fantasy-adventure-ai/`, and
  rebuild with `docker compose --profile production up -d --build`.
- **502 under `/fantasy-adventure-ai/`**: the app's `web` container isn't
  reachable from the edge - check `docker compose ps` in both projects and
  that `web` is attached to the `edge` network.
- **Logged out right after logging in**: `SESSION_COOKIE_PATH` in the app's
  `.env` doesn't match the prefix in use (or `ENVIRONMENT=production` is set
  while browsing over plain HTTP, so the `Secure` cookie is dropped).
- **502 from the API**: confirm the `api` container is healthy and running
  (`docker compose ps`) - check `docker compose logs api` for a migration
  failure on startup (step 6a) if it's exiting immediately.
- **Docker commands need `sudo`**: you weren't re-added to the `docker`
  group correctly, or haven't logged back in since bootstrap.sh ran - see
  step 5.
