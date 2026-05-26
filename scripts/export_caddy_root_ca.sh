#!/usr/bin/env bash
# Экспорт корневого сертификата Caddy (local CA) для установки на ПК/телефон.
# После установки https://vaultwarden.home.arpa будет «защищённым» в браузере.
set -euo pipefail

OUT="${1:-$HOME/caddy-homelab-root.crt}"

if ! docker ps --format '{{.Names}}' | grep -qx caddy; then
  echo "Контейнер caddy не запущен. Сначала: ./scripts/30_deploy_proxy_caddy.sh"
  exit 1
fi

docker exec caddy cat /data/caddy/pki/authorities/local/root.crt >"$OUT"
chmod 644 "$OUT"

echo "Сохранено: $OUT"
echo ""
echo "Установка:"
echo "  • Windows: certmgr.msc → Доверенные корневые → Импорт → $OUT"
echo "  • Firefox: Настройки → Приватность → Сертификаты → Просмотр → Центры → Импорт"
echo "  • Linux (Debian/Ubuntu): sudo cp $OUT /usr/local/share/ca-certificates/caddy-homelab.crt && sudo update-ca-certificates"
echo "  • macOS: sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain $OUT"
echo ""
echo "Перезапустите браузер и откройте: https://vaultwarden.home.arpa"
