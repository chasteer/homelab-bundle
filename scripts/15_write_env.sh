#!/usr/bin/env bash
# Обёртка: см. scripts/write_env.sh или ./setup.sh
set -euo pipefail
exec "$(dirname "$0")/write_env.sh"
