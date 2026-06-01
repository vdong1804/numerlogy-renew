#!/usr/bin/env bash
# =============================================================================
# deploy.sh — one-command deploy for ALL Numerology projects.
#
#   pull latest code → build frontend + api images → migrate db → restart stack
#
# Usage (on the server, from this deploy/ dir):
#   bash deploy.sh
#
# Prereqs (first time): run ./init-letsencrypt.sh once to obtain TLS certs,
# and create ./.env.prod from .env.prod.example.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE="docker compose -f $SCRIPT_DIR/docker-compose.prod.yml --env-file $SCRIPT_DIR/.env.prod"

cd "$SCRIPT_DIR"

if [ ! -f ./.env.prod ]; then
  echo "ERROR: .env.prod not found. Copy it first:"
  echo "    cp .env.prod.example .env.prod && \$EDITOR .env.prod"
  exit 1
fi

echo "==> Pulling latest code..."
git -C "$REPO_ROOT" pull --rebase || echo "    (skipped git pull — not a clean tree or no remote)"

echo "==> Building images (frontend + api)..."
# NEXT_PUBLIC_* build args come from .env.prod via --env-file above.
$COMPOSE build frontend api

echo "==> Starting database..."
$COMPOSE up -d db

echo "==> Waiting for database to be healthy..."
timeout 90 bash -c "until [ \"\$(docker inspect -f '{{.State.Health.Status}}' \$($COMPOSE ps -q db) 2>/dev/null)\" = healthy ]; do sleep 2; done"

echo "==> Running Alembic migrations..."
$COMPOSE run --rm api alembic upgrade head

echo "==> (Re)starting all services..."
$COMPOSE up -d

echo "==> Pruning dangling images..."
docker image prune -f >/dev/null

echo ""
echo "==> Deploy complete!"
echo "    Frontend : https://nhansinhquan.vn"
echo "    API      : https://api.nhansinhquan.vn/health"
echo "    CMS      : https://cms.nhansinhquan.vn"
echo "    Logs     : $COMPOSE logs -f"
