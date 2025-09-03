#!/usr/bin/env bash
set -euo pipefail
sudo mkdir -p /srv/{media/{library,downloads,config/{jellyfin,torrserver},cache},photos/{library,db},secrets/vaultwarden,homelab/uptime-kuma,immich/{cache,ml}}
sudo chown -R $USER:$USER /srv
echo "Created /srv layout with TorrServer directories."
