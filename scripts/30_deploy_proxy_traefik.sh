#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../proxy"
docker compose -f docker-compose.traefik.yml up -d
echo "Traefik up at http://*.home.arpa"
