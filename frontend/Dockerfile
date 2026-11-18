FROM node:24-slim AS builder

WORKDIR /app

# Dependency-only layer first, so `docker build` can reuse the cached layer
# when only application code (not package.json/package-lock.json) changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Public path the built app is served under (must match the reverse proxy's
# prefix, including leading and trailing slash). Defaults to the domain root.
ARG VITE_BASE_PATH=/
RUN npm run build

# caddy:2-alpine's own default CMD already runs `caddy run` against
# /etc/caddy/Caddyfile - Task 50's docker-compose `web` service mounts
# deploy/Caddyfile there. Nothing to configure here beyond the static files.
FROM caddy:2.11-alpine

COPY --from=builder /app/dist /srv
