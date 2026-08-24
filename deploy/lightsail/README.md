# Deploying to AWS Lightsail

A complete, from-scratch guide to running Fantasy AI Adventure on a single
AWS Lightsail instance: no managed database, no load balancer, no other
AWS services required.

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
game from, pointing at the static IP from step 2. This can be done either
through Lightsail's own DNS zone (**Networking → DNS zones**) or through
your existing registrar/DNS provider - whichever already manages the
domain.

DNS propagation can take anywhere from a few minutes to 48 hours. Confirm
it's resolved (`dig +short your-domain.example.com` or
`nslookup your-domain.example.com`) before continuing - Caddy's automatic
HTTPS (step 6) will fail to obtain a certificate if the domain doesn't yet
resolve to this instance.

## 4. Configure the firewall

Lightsail console → your instance → **Networking** tab → **IPv4 Firewall**.
Only these three rules should be present:

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

```bash
cd /opt/fantasy-ai-adventure
nano .env   # or your editor of choice
```

At minimum, set:

- `GEMINI_API_KEY` - your real key (leave `LLM_PROVIDER=mock` instead if
  you want to run without one, at least initially).
- `SITE_ADDRESS` - the real domain from step 3 (e.g.
  `adventure.example.com`). This is what Caddy uses to request the Let's
  Encrypt certificate - it must already resolve to this instance's static
  IP.
- `ENVIRONMENT=production`.

Then start everything:

```bash
docker compose --profile production up -d --build
```

Note the `--profile production` flag - it's required. The `web` (Caddy)
service is gated behind that profile so that local development, which
never runs Caddy, doesn't accidentally build and start it too.

Watch the logs during first startup to confirm Caddy obtains its
certificate successfully:

```bash
docker compose logs -f web
```

Look for `certificate obtained successfully` in the output. If it never
appears, double-check DNS has propagated and the firewall allows port 80.

## 7. Run database migrations

The database schema doesn't exist until migrations run - do this once
after the first `up`:

```bash
cd /opt/fantasy-ai-adventure
docker compose exec api /app/.venv/bin/alembic upgrade head
```

(Not `uv run alembic ...` - the production image is hardened and doesn't
include `uv`; the venv's own `alembic` is already on `PATH` inside the
container.)

At this point the site should be live at `https://<your-domain>`.

## 8. Set up nightly backups

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

## 9. Test backup restoration

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
#    proving it's not just structurally valid but genuinely usable.
#    --user root: the production image runs as a non-root user (Task 49),
#    which won't have write access to a freshly-copied file it doesn't own
#    - root sidesteps that for this one-off diagnostic container.
mkdir -p /tmp/restore-test
cp "$BACKUP_FILE" /tmp/restore-test/game.db
docker run --rm -d --name restore-test --user root \
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

## Updating the deployment

```bash
cd /opt/fantasy-ai-adventure
git pull
docker compose --profile production up -d --build
```

Compose only recreates containers whose image actually changed, so this is
safe to run even when nothing changed.

## Troubleshooting

- **Caddy won't get a certificate**: confirm DNS resolves to the
  instance's static IP (`dig +short your-domain`), and that ports 80/443
  are open in the Lightsail firewall (step 4). Check
  `docker compose logs web` for the specific TLS error.
- **502 from the API**: confirm the `api` container is healthy
  (`docker compose ps`) and that migrations have been run (step 7).
- **Docker commands need `sudo`**: you weren't re-added to the `docker`
  group correctly, or haven't logged back in since bootstrap.sh ran - see
  step 5.
