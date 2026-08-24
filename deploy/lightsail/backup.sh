#!/usr/bin/env bash
# Nightly SQLite backup: takes a live-safe VACUUM INTO snapshot from inside
# the running `api` container (VACUUM INTO is a single atomic statement,
# safe against concurrent WAL writers, and compacts the copy), pulls it
# onto the host outside any Docker volume, then rotates it into 7-daily /
# 4-weekly retention tiers. Invoked nightly by fantasy-backup.timer via
# fantasy-backup.service (see deploy/systemd/).
set -euo pipefail

cd "$(dirname "$0")/../.."

BACKUP_ROOT="$(pwd)/backups"
DAILY_DIR="$BACKUP_ROOT/daily"
WEEKLY_DIR="$BACKUP_ROOT/weekly"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
SNAPSHOT_NAME="game-$TIMESTAMP.db"
CONTAINER_TMP="/tmp/$SNAPSHOT_NAME"

mkdir -p "$DAILY_DIR" "$WEEKLY_DIR"

echo "==> Taking a VACUUM INTO snapshot"
docker compose exec -T api python3 -c "
import sqlite3
sqlite3.connect('/data/game.db').execute(\"VACUUM INTO '$CONTAINER_TMP'\")
"

echo "==> Copying snapshot to $DAILY_DIR"
docker compose exec -T api cat "$CONTAINER_TMP" > "$DAILY_DIR/$SNAPSHOT_NAME"
docker compose exec -T api rm -f "$CONTAINER_TMP"

# Promote Sunday's daily snapshot into the weekly tier too (date +%u: 7 = Sunday).
if [ "$(date +%u)" = "7" ]; then
	echo "==> Promoting today's snapshot to $WEEKLY_DIR"
	cp "$DAILY_DIR/$SNAPSHOT_NAME" "$WEEKLY_DIR/$SNAPSHOT_NAME"
fi

echo "==> Rotating retention (7 daily / 4 weekly)"
find "$DAILY_DIR" -name '*.db' -mtime +7 -delete
find "$WEEKLY_DIR" -name '*.db' -mtime +28 -delete

echo "==> Backup complete: $DAILY_DIR/$SNAPSHOT_NAME"
