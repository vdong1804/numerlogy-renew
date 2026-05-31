#!/usr/bin/env bash
# deploy.sh — pull latest code, build API image, restart prod stack
# Usage (from VPS): bash deploy/deploy.sh
# Run once after initial letsencrypt cert is obtained.
set -euo pipefail

COMPOSE="docker compose -f docker-compose.prod.yml"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Entering deploy dir: $SCRIPT_DIR"
cd "$SCRIPT_DIR"

echo "==> Pulling latest code..."
git -C "$(dirname "$SCRIPT_DIR")" pull --rebase

echo "==> Building API image..."
$COMPOSE build api

echo "==> Starting db (if not already up)..."
$COMPOSE up -d db

echo "==> Waiting for db to be healthy..."
timeout 60 bash -c 'until docker compose -f docker-compose.prod.yml ps db | grep -q "healthy"; do sleep 2; done'

echo "==> Running Alembic migrations..."
$COMPOSE run --rm api alembic upgrade head

echo "==> Restarting all services..."
$COMPOSE up -d

echo "==> Pruning old/unused images..."
docker image prune -f

echo ""
echo "==> Deploy complete!"
echo "    Tail logs : $COMPOSE logs -f api"
echo "    Health    : curl https://cms.nhansinhquan.vn/health"
