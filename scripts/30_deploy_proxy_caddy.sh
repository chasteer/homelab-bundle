#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../proxy"
docker compose -f docker-compose.caddy.yml up -d
echo "Caddy up at https://*.home.arpa"
