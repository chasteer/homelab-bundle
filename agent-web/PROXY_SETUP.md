# Настройка прокси для Groq

## Обзор

Этот документ описывает, как настроить прокси-сервер для доступа к Groq API через VPS, если Groq заблокирован в вашей стране.

## Требования

- VPS с публичным IP
- Установленный прокси-сервер (TinyProxy, Squid, или другой)
- Открытые порты на VPS

## Настройка TinyProxy на VPS

### 1. Установка TinyProxy

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install tinyproxy

# CentOS/RHEL
sudo yum install tinyproxy
```

### 2. Конфигурация

Отредактируйте файл конфигурации:

```bash
sudo nano /etc/tinyproxy/tinyproxy.conf
```

Основные настройки:

```conf
# Порт прокси
Port 8888

# Слушать на всех интерфейсах
Listen 0.0.0.0

# Разрешить все IP (или укажите конкретные)
Allow 0.0.0.0/0

# Отключить аутентификацию (или настроить)
# User nobody
# Group nogroup

# Логирование
LogFile "/var/log/tinyproxy/tinyproxy.log"
LogLevel Info
```

### 3. Запуск сервиса

```bash
sudo systemctl enable tinyproxy
sudo systemctl start tinyproxy
sudo systemctl status tinyproxy
```

### 4. Настройка firewall

```bash
# UFW
sudo ufw allow 8888

# iptables
sudo iptables -A INPUT -p tcp --dport 8888 -j ACCEPT
```

## Настройка в проекте

### 1. Переменные окружения

Добавьте в `.env` файл:

```env
# Groq API
GROQ_API_KEY=your_groq_api_key_here

# Прокси настройки
PROXY_URL=http://your_vps_ip:8888
```

### 2. Проверка работы

Запустите тест:

```bash
docker exec homelab-agent python /app/test_groq_models.py
```

## Альтернативные прокси-серверы

### Squid

```bash
# Установка
sudo apt install squid

# Конфигурация
sudo nano /etc/squid/squid.conf

# Основные настройки
http_port 8888
http_access allow all
```

### Nginx (как прокси)

```nginx
server {
    listen 8888;
    location / {
        proxy_pass https://api.groq.com;
        proxy_set_header Host api.groq.com;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Устранение неполадок

### Прокси не отвечает

1. Проверьте статус сервиса:
   ```bash
   sudo systemctl status tinyproxy
   ```

2. Проверьте логи:
   ```bash
   sudo tail -f /var/log/tinyproxy/tinyproxy.log
   ```

3. Проверьте порт:
   ```bash
   sudo netstat -tlnp | grep 8888
   ```

### 403 Access Denied

1. Проверьте конфигурацию `Allow` в tinyproxy.conf
2. Убедитесь, что IP разрешен
3. Проверьте firewall на VPS

### Таймауты

1. Проверьте сетевую связность
2. Увеличьте timeout в настройках
3. Проверьте нагрузку на VPS

## Безопасность

⚠️ **Важно**: Открытый прокси без аутентификации может быть использован злоумышленниками.

### Рекомендации:

1. Используйте аутентификацию
2. Ограничьте доступ по IP
3. Регулярно обновляйте сервер
4. Мониторьте логи

### Настройка аутентификации

```conf
# В tinyproxy.conf
User nobody
Group nogroup
BasicAuth username password
```

## Мониторинг

### Логи TinyProxy

```bash
# Просмотр логов
sudo tail -f /var/log/tinyproxy/tinyproxy.log

# Статистика
sudo systemctl status tinyproxy
```

### Проверка подключений

```bash
# Активные соединения
sudo netstat -an | grep 8888

# Процессы
sudo ps aux | grep tinyproxy
```

## Заключение

Прокси-сервер позволяет обойти географические ограничения и использовать Groq API из любой страны. Следуйте рекомендациям по безопасности и регулярно мониторьте работу сервера.
