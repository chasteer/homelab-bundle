# 🚀 Установка Homelab VPS API

## 📋 Требования

- Ubuntu Server 20.04+ или 22.04+
- PHP 8.4-FPM
- Nginx
- Root доступ или sudo права
- Домен (для SSL)

## 🔧 Подготовка системы

### 1. Обновите систему
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Установите необходимые пакеты
```bash
sudo apt install -y curl wget git unzip nginx php8.4-fpm php8.4-common php8.4-curl php8.4-mbstring php8.4-zip
```

### 3. Проверьте версии
```bash
php -v
nginx -v
```

## 📥 Установка Homelab VPS API

### 1. Клонируйте проект
```bash
cd /tmp
git clone https://github.com/your-username/homelab-vps.git
cd homelab-vps
```

### 2. Запустите установщик
```bash
chmod +x install.sh
sudo ./install.sh
```

### 3. Проверьте установку
```bash
# Проверьте статус сервисов
sudo systemctl status nginx
sudo systemctl status php8.4-fpm

# Проверьте директории
ls -la /var/www/homelab-vps/
```

## ⚙️ Настройка

### 1. Отредактируйте .env файл
```bash
sudo nano /var/www/homelab-vps/.env
```

Заполните обязательные поля:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
API_SECRET_KEY=your_secret_key_here
ENVIRONMENT=production
```

### 2. Настройте домен в Nginx
```bash
sudo nano /etc/nginx/sites-available/homelab-vps
```

Замените `your-vps-domain.com` на ваш реальный домен.

### 3. Перезапустите сервисы
```bash
sudo systemctl restart nginx
sudo systemctl restart php8.4-fpm
```

## 🔐 Настройка SSL

### 1. Установите Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Получите SSL сертификат
```bash
sudo certbot --nginx -d your-domain.com
```

### 3. Проверьте автообновление
```bash
sudo certbot renew --dry-run
```

## 🧪 Тестирование

### 1. Проверьте API endpoints
```bash
# Тест
curl https://your-domain.com/api/test

# Статус
curl https://your-domain.com/api/status

# Здоровье
curl https://your-domain.com/api/health
```

### 2. Проверьте логи
```bash
# Логи приложения
sudo tail -f /var/www/homelab-vps/logs/homelab-vps.log

# Логи Nginx
sudo tail -f /var/log/nginx/homelab-vps.access.log
sudo tail -f /var/log/nginx/homelab-vps.error.log
```

## 🔧 Настройка Homelab Agent

### 1. Обновите .env файл агента
```bash
# В вашем Homelab
nano agent-web/.env
```

Добавьте:
```env
VPS_WEBHOOK_URL=https://your-domain.com/api/uptime-alerts
```

### 2. Перезапустите агента
```bash
sudo docker compose -f agent-web/docker-compose.yml restart agent
```

## 📱 Настройка Telegram Bot

Следуйте инструкции в [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)

## 🔍 Мониторинг

### 1. Проверьте статус сервисов
```bash
sudo systemctl status homelab-vps-monitor
```

### 2. Настройте логирование
```bash
# Автоматическая ротация логов
sudo nano /etc/logrotate.d/homelab-vps
```

Добавьте:
```
/var/www/homelab-vps/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

## 🚨 Устранение неполадок

### Проблема: Nginx не запускается
```bash
# Проверьте конфигурацию
sudo nginx -t

# Проверьте логи
sudo tail -f /var/log/nginx/error.log
```

### Проблема: PHP-FPM не работает
```bash
# Проверьте статус
sudo systemctl status php8.4-fpm

# Проверьте конфигурацию
sudo php-fpm8.4 -t
```

### Проблема: Права доступа
```bash
# Исправьте права
sudo chown -R www-data:www-data /var/www/homelab-vps
sudo chmod -R 755 /var/www/homelab-vps
sudo chmod 640 /var/www/homelab-vps/.env
```

### Проблема: SSL сертификат
```bash
# Проверьте сертификат
sudo certbot certificates

# Обновите вручную
sudo certbot renew
```

## 🔒 Безопасность

### 1. Настройте firewall
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Настройте fail2ban
```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Регулярные обновления
```bash
# Добавьте в crontab
sudo crontab -e

# Добавьте строку:
0 2 * * * /usr/bin/apt update && /usr/bin/apt upgrade -y
```

## 📊 Мониторинг производительности

### 1. Установите htop
```bash
sudo apt install -y htop
```

### 2. Мониторинг ресурсов
```bash
# CPU и память
htop

# Дисковое пространство
df -h

# Сетевые соединения
ss -tulpn
```

## 🔄 Обновления

### 1. Обновление кода
```bash
cd /tmp
git clone https://github.com/your-username/homelab-vps.git
sudo cp -r homelab-vps/api/* /var/www/homelab-vps/api/
sudo chown -R www-data:www-data /var/www/homelab-vps
sudo systemctl restart php8.4-fpm
```

### 2. Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
sudo systemctl restart nginx php8.4-fpm
```

## 📚 Полезные команды

```bash
# Перезапуск всех сервисов
sudo systemctl restart nginx php8.4-fpm

# Проверка статуса
sudo systemctl status nginx php8.4-fpm homelab-vps-monitor

# Просмотр логов в реальном времени
sudo tail -f /var/www/homelab-vps/logs/homelab-vps.log

# Проверка конфигурации Nginx
sudo nginx -t

# Тест API
curl -X POST https://your-domain.com/api/uptime-alerts \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}'
```

---

**Установка завершена! Теперь ваш VPS готов принимать уведомления от Homelab!** 🎉
