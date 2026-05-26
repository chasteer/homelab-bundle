

echo "🔌 Проверка открытых портов..."
echo "Порты, которые должны быть открыты:"
echo "  8090: TorrServer"
echo "  2283: Immich"
echo "  8081: Vaultwarden"
echo "  3001: Uptime Kuma"
echo "  8096: Jellyfin"
echo "  8000: Homelab Agent"

echo ""
echo "🔍 Проверка активных портов:"
if command -v netstat >/dev/null 2>&1; then
    netstat -tlnp | grep -E ':(8090|2283|8081|3001|8096|8000)' | sort || echo "Активные порты не найдены"
elif command -v ss >/dev/null 2>&1; then
    ss -tlnp | grep -E ':(8090|2283|8081|3001|8096|8000)' | sort || echo "Активные порты не найдены"
else
    echo "⚠️  netstat и ss недоступны"
fi

# Проверяем доступность веб-интерфейсов
echo ""
echo "🌐 Доступность веб-интерфейсов:"

check_web_interface() {
    local name="$1"
    local url="$2"
    
    if curl -f -s "$url" >/dev/null 2>&1; then
        echo "   ✅ $name: $url"
    else
        echo "   ❌ $name: $url (недоступен)"
    fi
}

check_web_interface "Jellyfin" "http://${HOMELAB_HOST:-your_local_ip}:8096"
check_web_interface "TorrServer" "http://${HOMELAB_HOST:-your_local_ip}:8090"
check_web_interface "Immich" "http://${HOMELAB_HOST:-your_local_ip}:2283"
check_web_interface "Vaultwarden" "http://${HOMELAB_HOST:-your_local_ip}:8081"
check_web_interface "Uptime Kuma" "http://${HOMELAB_HOST:-your_local_ip}:3001"
check_web_interface "Homelab Agent API" "http://${HOMELAB_HOST:-your_local_ip}:8000/api/health"

if command -v curl >/dev/null 2>&1; then
  echo ""
  echo "🔒 HTTPS (*.home.arpa, нужен hosts/DNS):"
  for pair in "Jellyfin|https://jellyfin.home.arpa" "Dozzle|https://dozzle.home.arpa" "it-tools|https://it-tools.home.arpa" "Home Assistant|https://homeassistant.home.arpa"; do
    name="${pair%%|*}"
    url="${pair##*|}"
    if curl -fk -s "$url" >/dev/null 2>&1; then
      echo "   ✅ $name: $url"
    else
      echo "   ⚠️  $name: $url (проверьте DNS и ./scripts/30_deploy_proxy_caddy.sh)"
    fi
  done
fi
