#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$0")/.."
cd "$ROOT/proxy"

if [[ -f ../services/.env ]]; then
  set -a
  # shellcheck source=/dev/null
  source ../services/.env
  set +a
fi

ACME_EMAIL_BLOCK=""
PUBLIC_DOMAIN_BLOCK=""

if [[ -n "${VW_PUBLIC_DOMAIN:-}" ]]; then
  if [[ -z "${ACME_EMAIL:-}" ]]; then
    echo "❌ Для Let's Encrypt задайте ACME_EMAIL в services/.env"
    exit 1
  fi
  ACME_EMAIL_BLOCK=$'	email '"${ACME_EMAIL}"
  PUBLIC_DOMAIN_BLOCK="${VW_PUBLIC_DOMAIN} {
	encode gzip
	reverse_proxy http://vaultwarden:80 {
		header_up X-Real-IP {remote_host}
		header_up X-Forwarded-For {remote_host}
		header_up X-Forwarded-Proto {scheme}
	}
}"
  echo "🔐 Let's Encrypt для ${VW_PUBLIC_DOMAIN} (нужны проброс 80/443 и DNS A-запись)"
else
  echo "🔐 LAN: tls internal (*.home.arpa). Доверьте CA: ../scripts/export_caddy_root_ca.sh"
fi

python3 - <<PY
import os
from pathlib import Path

tpl = Path("Caddyfile.template").read_text()
out = tpl.replace("{{ACME_EMAIL_BLOCK}}", os.environ.get("ACME_EMAIL_BLOCK", ""))
out = out.replace("{{PUBLIC_DOMAIN_BLOCK}}", os.environ.get("PUBLIC_DOMAIN_BLOCK", ""))
Path("Caddyfile").write_text(out)
PY

docker compose -f docker-compose.caddy.yml up -d --force-recreate caddy
echo "Caddy на ${HOMELAB_HOST:-0.0.0.0}:443 (HTTPS без отдельного логина)"
echo "Vaultwarden: ${VW_DOMAIN:-https://vaultwarden.home.arpa}"
