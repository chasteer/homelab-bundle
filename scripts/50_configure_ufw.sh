#!/usr/bin/env bash
set -euo pipefail
LAN_CIDR="${1:-192.168.0.0/16}"

echo "🔒 Настройка UFW для Homelab..."

# Настройка UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH доступ
sudo ufw allow from "$LAN_CIDR" to any port 22 proto tcp

# Порты для сервисов homelab
for p in 80 443 8096 8090 2283 8081 3001 8000; do
  if [[ "$p" == "6881" ]]; then 
    sudo ufw allow from "$LAN_CIDR" to any port $p
    echo "✅ UFW: порт $p (UDP/TCP) открыт для $LAN_CIDR"
  else 
    sudo ufw allow from "$LAN_CIDR" to any port $p proto tcp
    echo "✅ UFW: порт $p (TCP) открыт для $LAN_CIDR"
  fi
done

# Включаем UFW
sudo ufw enable

echo ""
echo "🔒 UFW настроен и включен"
echo "📊 Статус:"
sudo ufw status verbose

echo ""
echo "📋 Открытые порты:"
echo "   - 22: SSH"
echo "   - 80: HTTP (прокси)"
echo "   - 443: HTTPS (прокси)"
echo "   - 8096: Jellyfin"
echo "   - 8090: TorrServer"
echo "   - 2283: Immich"
echo "   - 8081: Vaultwarden"
echo "   - 3001: Uptime Kuma"
echo "   - 8000: Homelab Agent"
