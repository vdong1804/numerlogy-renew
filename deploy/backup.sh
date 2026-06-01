#!/usr/bin/env bash
# =============================================================================
# backup.sh — daily Postgres dump with 14-day rotation.
#
# Install via cron (crontab -e):
#   0 2 * * * /path/to/Numerlogy/deploy/backup.sh >> /var/log/numerology-backup.log 2>&1
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="docker compose -f $SCRIPT_DIR/docker-compose.prod.yml --env-file $SCRIPT_DIR/.env.prod"
BACKUP_DIR="$SCRIPT_DIR/backups"
RETENTION_DAYS=14

# shellcheck disable=SC1091
set -a; . "$SCRIPT_DIR/.env.prod"; set +a

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$BACKUP_DIR/numerology-$STAMP.sql.gz"

echo "==> Dumping database to $OUT"
$COMPOSE exec -T db pg_dump -U "${POSTGRES_USER:-numerology}" "${POSTGRES_DB:-numerology}" | gzip > "$OUT"

echo "==> Pruning dumps older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name 'numerology-*.sql.gz' -mtime +"$RETENTION_DAYS" -delete

echo "==> Backup complete: $(du -h "$OUT" | cut -f1)"
