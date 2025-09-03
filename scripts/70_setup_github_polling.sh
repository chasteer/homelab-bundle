#!/usr/bin/env bash
set -euo pipefail

# Скрипт для настройки GitHub polling
# Проверяет репозитории на наличие новых PR/MR и запускает анализ

cd "$(dirname "$0")/.."

# Создаем директорию для конфигурации
mkdir -p /etc/homelab/github

# Создаем конфигурационный файл для GitHub polling
cat > /etc/homelab/github/polling.conf << 'EOF'
# Конфигурация GitHub polling для Homelab Agent
# Формат: owner/repo:branch:webhook_url:secret

# Примеры:
# microsoft/vscode:main:https://your-domain.com/webhook/github:your_secret
# username/project:develop:https://your-domain.com/webhook/github:your_secret

# Добавьте свои репозитории ниже:
# owner/repo:branch:webhook_url:secret
EOF

# Создаем systemd сервис для GitHub polling
cat > /etc/systemd/system/github-polling.service << 'EOF'
[Unit]
Description=GitHub Polling Service for Homelab Agent
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
ExecStart=/usr/bin/python3 /root/github_polling.py
Restart=always
RestartSec=60
Environment=GITHUB_TOKEN=your_github_token_here
Environment=POLLING_INTERVAL=300

[Install]
WantedBy=multi-user.target
EOF

# Создаем Python скрипт для polling
cat > /root/github_polling.py << 'EOF'
#!/usr/bin/env/python3
"""
GitHub Polling Service для Homelab Agent
Проверяет репозитории на наличие новых PR/MR
"""

import os
import time
import requests
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/github-polling.log'),
        logging.StreamHandler()
    ]
)

class GitHubPoller:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.polling_interval = int(os.getenv('POLLING_INTERVAL', 300))  # 5 минут по умолчанию
        self.config_file = '/etc/homelab/github/polling.conf'
        self.last_check_file = '/var/lib/homelab/github_last_check.json'
        
        if not self.github_token:
            logging.error("GITHUB_TOKEN не задан")
            raise ValueError("GITHUB_TOKEN не задан")
        
        # Создаем директорию для хранения состояния
        Path('/var/lib/homelab').mkdir(parents=True, exist_ok=True)
        
        # Загружаем последние проверки
        self.last_checks = self.load_last_checks()
    
    def load_last_checks(self):
        """Загрузка времени последних проверок"""
        try:
            if Path(self.last_check_file).exists():
                with open(self.last_check_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.warning(f"Ошибка загрузки последних проверок: {e}")
        
        return {}
    
    def save_last_checks(self):
        """Сохранение времени последних проверок"""
        try:
            with open(self.last_check_file, 'w') as f:
                json.dump(self.last_checks, f)
        except Exception as e:
            logging.error(f"Ошибка сохранения последних проверок: {e}")
    
    def load_config(self):
        """Загрузка конфигурации репозиториев"""
        repos = []
        try:
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 3:
                            owner_repo = parts[0]
                            branch = parts[1]
                            webhook_url = parts[2]
                            secret = parts[3] if len(parts) > 3 else None
                            
                            if '/' in owner_repo:
                                owner, repo = owner_repo.split('/', 1)
                                repos.append({
                                    'owner': owner,
                                    'repo': repo,
                                    'branch': branch,
                                    'webhook_url': webhook_url,
                                    'secret': secret
                                })
        except Exception as e:
            logging.error(f"Ошибка загрузки конфигурации: {e}")
        
        return repos
    
    def check_repository(self, repo_config):
        """Проверка репозитория на новые PR/MR"""
        try:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Получаем последние PR
            pr_url = f"https://api.github.com/repos/{repo_config['owner']}/{repo_config['repo']}/pulls"
            params = {
                'state': 'open',
                'sort': 'updated',
                'direction': 'desc',
                'per_page': 10
            }
            
            response = requests.get(pr_url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                logging.warning(f"Ошибка получения PR для {repo_config['owner']}/{repo_config['repo']}: {response.status_code}")
                return
            
            prs = response.json()
            
            for pr in prs:
                pr_key = f"{repo_config['owner']}/{repo_config['repo']}#{pr['number']}"
                last_updated = pr['updated_at']
                
                # Проверяем, был ли уже проверен этот PR
                if pr_key in self.last_checks:
                    last_check = self.last_checks[pr_key]
                    if last_check >= last_updated:
                        continue
                
                # Новый или обновленный PR
                logging.info(f"Найден новый/обновленный PR: {pr_key}")
                
                # Отправляем webhook
                self.send_webhook(repo_config, pr)
                
                # Обновляем время последней проверки
                self.last_checks[pr_key] = last_updated
                
        except Exception as e:
            logging.error(f"Ошибка проверки репозитория {repo_config['owner']}/{repo_config['repo']}: {e}")
    
    def send_webhook(self, repo_config, pr):
        """Отправка webhook для анализа PR"""
        try:
            webhook_data = {
                'action': 'opened',
                'pull_request': pr,
                'repository': {
                    'owner': {'login': repo_config['owner']},
                    'name': repo_config['repo']
                }
            }
            
            headers = {'Content-Type': 'application/json'}
            if repo_config['secret']:
                # В реальной реализации здесь должна быть подпись
                pass
            
            response = requests.post(
                repo_config['webhook_url'],
                json=webhook_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logging.info(f"Webhook отправлен для {repo_config['owner']}/{repo_config['repo']}#{pr['number']}")
            else:
                logging.warning(f"Ошибка отправки webhook: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Ошибка отправки webhook: {e}")
    
    def run(self):
        """Основной цикл polling"""
        logging.info("GitHub Polling Service запущен")
        
        while True:
            try:
                repos = self.load_config()
                
                if not repos:
                    logging.info("Нет репозиториев для проверки")
                else:
                    logging.info(f"Проверяем {len(repos)} репозиториев")
                    
                    for repo_config in repos:
                        self.check_repository(repo_config)
                        time.sleep(1)  # Небольшая пауза между запросами
                    
                    # Сохраняем состояние
                    self.save_last_checks()
                
                logging.info(f"Ожидание {self.polling_interval} секунд до следующей проверки")
                time.sleep(self.polling_interval)
                
            except KeyboardInterrupt:
                logging.info("Получен сигнал остановки")
                break
            except Exception as e:
                logging.error(f"Критическая ошибка: {e}")
                time.sleep(60)  # Пауза перед повторной попыткой

if __name__ == '__main__':
    poller = GitHubPoller()
    poller.run()
EOF

# Делаем скрипт исполняемым
chmod +x /root/github_polling.py

# Перезагружаем systemd
systemctl daemon-reload

# Включаем сервис
systemctl enable github-polling.service

echo "✅ GitHub Polling Service настроен"
echo "📝 Отредактируйте /etc/homelab/github/polling.conf для добавления репозиториев"
echo "🔑 Установите GITHUB_TOKEN в /etc/systemd/system/github-polling.service"
echo "🚀 Запустите сервис: systemctl start github-polling.service"
echo "📊 Проверьте логи: journalctl -u github-polling.service -f"
