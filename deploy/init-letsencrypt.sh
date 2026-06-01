#!/usr/bin/env bash
# =============================================================================
# init-letsencrypt.sh — obtain the initial TLS certificate (run ONCE).
#
# Issues a single Let's Encrypt cert covering all four subdomains:
#   nhansinhquan.vn, www., api., cms.
#
# Flow: drop a dummy self-signed cert so nginx can boot → start nginx →
# delete dummy → request the real cert over the HTTP-01 webroot challenge →
# reload nginx. After this, the certbot service auto-renews.
#
# Prereqs: DNS A records for all 4 subdomains point to THIS server, ports
# 80/443 open, ./.env.prod exists.
#
# Usage:
#   bash init-letsencrypt.sh you@email.com
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE="docker compose -f $SCRIPT_DIR/docker-compose.prod.yml --env-file $SCRIPT_DIR/.env.prod"

PRIMARY_DOMAIN="nhansinhquan.vn"
DOMAINS=(nhansinhquan.vn www.nhansinhquan.vn api.nhansinhquan.vn cms.nhansinhquan.vn)
EMAIL="${1:-}"
STAGING="${STAGING:-0}"   # set STAGING=1 to test against LE staging (avoids rate limits)

CERT_PATH="./certbot/conf/live/$PRIMARY_DOMAIN"

if [ -z "$EMAIL" ]; then
  echo "ERROR: pass an email for Let's Encrypt expiry notices:"
  echo "    bash init-letsencrypt.sh you@email.com"
  exit 1
fi

mkdir -p ./certbot/conf ./certbot/www

if [ -d "$CERT_PATH" ]; then
  read -r -p "Existing cert found for $PRIMARY_DOMAIN. Replace it? (y/N) " ans
  [ "$ans" = "y" ] || { echo "Aborted."; exit 0; }
fi

echo "==> Creating dummy certificate so nginx can start..."
mkdir -p "$CERT_PATH"
# certbot image has ENTRYPOINT ["certbot"], so override it to call openssl.
docker run --rm --entrypoint openssl \
  -v "$SCRIPT_DIR/certbot/conf:/etc/letsencrypt" certbot/certbot \
  req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "/etc/letsencrypt/live/$PRIMARY_DOMAIN/privkey.pem" \
    -out "/etc/letsencrypt/live/$PRIMARY_DOMAIN/fullchain.pem" \
    -subj "/CN=localhost"

echo "==> Starting nginx with dummy cert..."
$COMPOSE up -d nginx

echo "==> Deleting dummy certificate..."
docker run --rm --entrypoint sh \
  -v "$SCRIPT_DIR/certbot/conf:/etc/letsencrypt" certbot/certbot \
  -c "rm -rf /etc/letsencrypt/live/$PRIMARY_DOMAIN \
             /etc/letsencrypt/archive/$PRIMARY_DOMAIN \
             /etc/letsencrypt/renewal/$PRIMARY_DOMAIN.conf"

echo "==> Requesting real certificate from Let's Encrypt..."
domain_args=""
for d in "${DOMAINS[@]}"; do domain_args="$domain_args -d $d"; done

staging_arg=""
[ "$STAGING" != "0" ] && staging_arg="--staging"

docker run --rm \
  -v "$SCRIPT_DIR/certbot/conf:/etc/letsencrypt" \
  -v "$SCRIPT_DIR/certbot/www:/var/www/certbot" \
  certbot/certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    --email "$EMAIL" --agree-tos --no-eff-email \
    --cert-name "$PRIMARY_DOMAIN" \
    --force-renewal \
    $domain_args

echo "==> Reloading nginx with the real certificate..."
$COMPOSE exec nginx nginx -s reload

echo ""
echo "==> Done. Certificate issued for: ${DOMAINS[*]}"
echo "    Now run: bash deploy.sh"
