#!/usr/bin/env bash
set -euo pipefail
for H in jellyfin.home.arpa qb.home.arpa immich.home.arpa vaultwarden.home.arpa kuma.home.arpa agent.home.arpa; do
  if grep -q "$H" /etc/hosts; then sudo sed -i "s/^.*\s$H$/${HOMELAB_HOST:-your_local_ip} $H/" /etc/hosts; else echo "${HOMELAB_HOST:-your_local_ip} $H" | sudo tee -a /etc/hosts >/dev/null; fi
done
echo "Done."
