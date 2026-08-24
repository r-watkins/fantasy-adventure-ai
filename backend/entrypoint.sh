#!/bin/sh
# Runs as root (the image's non-root USER directive was removed so this can
# work), fixes ownership of the mounted /data volume, then drops to the
# unprivileged `app` user before exec'ing the real command.
#
# Found live (Task 57): Docker creates named volumes root-owned by default.
# On a fresh volume (a real first deploy, or any local `docker volume rm`),
# the hardened image's non-root `app` user (Task 49) had no write access to
# /data at all - `alembic upgrade head` and every DB write failed with
# "unable to open database file". This is the standard fix for a non-root
# container + a freshly-created bind/named volume: start as root just long
# enough to chown the mount, then hand off.
set -e

mkdir -p /data
chown -R app:app /data

exec runuser -u app -- "$@"
