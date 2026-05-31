#!/usr/bin/env bash
# backup.sh — daily Postgres backup with 14-day rotation
# Suggested crontab (as root or deploy user):
#   0 2 * * * /opt/numerology-api/deploy/backup.sh >> /var/log/numerology-backup.log 2>&1
set -euo pipefail

COMPOSE_FILE="/opt/numerology-api/deploy/docker-compose.prod.yml"
BACKUP_DIR="/backup/numerology"
DATE="$(date +%F)"

mkdir -p "$BACKUP_DIR"

echo "[$(date -Is)] Starting backup..."

docker compose -f "$COMPOSE_FILE" exec -T db \
    pg_dump -U numerology numerology \
    | gzip > "$BACKUP_DIR/db-$DATE.sql.gz"

echo "[$(date -Is)] Backup written: $BACKUP_DIR/db-$DATE.sql.gz"

# Rotate: delete dumps older than 14 days
find "$BACKUP_DIR" -name 'db-*.sql.gz' -mtime +14 -delete
echo "[$(date -Is)] Rotation complete (kept 14 days)."

# Optional: verify file is non-empty
SIZE=$(stat -c%s "$BACKUP_DIR/db-$DATE.sql.gz" 2>/dev/null || echo 0)
if [ "$SIZE" -lt 100 ]; then
    echo "[$(date -Is)] WARNING: backup file suspiciously small ($SIZE bytes)"
    exit 1
fi

echo "[$(date -Is)] Done. Size: $SIZE bytes"
