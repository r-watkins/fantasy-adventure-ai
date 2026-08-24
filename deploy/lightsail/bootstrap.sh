#!/usr/bin/env bash
# One-time setup for a fresh AWS Lightsail Ubuntu 24.04 LTS instance:
# installs Docker Engine + the Compose plugin, grants the invoking user
# passwordless `docker` access, clones this repo to /opt/fantasy-ai-adventure,
# and creates a starter .env. Safe to re-run (idempotent).
#
# Usage: on the instance, as the default `ubuntu` user (or any sudo-capable
# user): curl -fsSL <raw-url-of-this-file> | bash
# or: git clone the repo somewhere temporary first, then run this script.
set -euo pipefail

REPO_URL="https://github.com/r-watkins/fantasy-adventure-ai.git"
INSTALL_DIR="/opt/fantasy-ai-adventure"
# $USER isn't reliably set in every invocation context (confirmed: unset
# under a plain `docker exec`, and non-login-shell invocations in general
# can't be relied on to have it) - whoami reflects the actual effective
# user regardless.
INVOKING_USER="$(whoami)"

echo "==> Installing prerequisites"
sudo apt update
sudo apt install -y ca-certificates curl git

echo "==> Setting up Docker's official apt repository"
sudo install -m 0755 -d /etc/apt/keyrings
if [ ! -f /etc/apt/keyrings/docker.asc ]; then
	sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
	sudo chmod a+r /etc/apt/keyrings/docker.asc
fi

sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update

echo "==> Installing Docker Engine + Compose plugin"
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo systemctl enable --now docker.service
sudo systemctl enable --now containerd.service

echo "==> Granting $INVOKING_USER passwordless docker access"
# docker-ce's own postinstall already creates the `docker` group - this is
# just a safety net in case that ever changes.
if ! getent group docker > /dev/null; then
	sudo groupadd docker
fi
if ! id -nG "$INVOKING_USER" | grep -qw docker; then
	sudo usermod -aG docker "$INVOKING_USER"
	NEEDS_RELOGIN=1
fi

echo "==> Cloning the repository to $INSTALL_DIR"
if [ -d "$INSTALL_DIR/.git" ]; then
	echo "    Already present - pulling latest instead of cloning."
	git -C "$INSTALL_DIR" pull --ff-only
else
	sudo mkdir -p "$INSTALL_DIR"
	sudo chown "$INVOKING_USER":"$INVOKING_USER" "$INSTALL_DIR"
	git clone "$REPO_URL" "$INSTALL_DIR"
fi

echo "==> Preparing .env"
if [ ! -f "$INSTALL_DIR/.env" ]; then
	cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
	echo "    Created $INSTALL_DIR/.env from .env.example - edit it with real values before deploying."
else
	echo "    $INSTALL_DIR/.env already exists - left untouched."
fi

echo ""
echo "==> Bootstrap complete."
if [ "${NEEDS_RELOGIN:-0}" = "1" ]; then
	echo "    Log out and back in (or run 'newgrp docker') to use docker without sudo."
fi
echo "    Next steps:"
echo "      1. Edit $INSTALL_DIR/.env - set GEMINI_API_KEY and SITE_ADDRESS (your real domain) at minimum."
echo "      2. cd $INSTALL_DIR && docker compose --profile production up -d --build"
echo "      3. Run migrations: docker compose exec api /app/.venv/bin/alembic upgrade head"
