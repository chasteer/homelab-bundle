FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    docker-compose \
    git \
    netcat-openbsd \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN useradd -m -s /bin/bash agent && \
    usermod -aG docker agent

# Создаем рабочие директории
WORKDIR /app
RUN mkdir -p /app/data /app/logs /app/github-config

# Копируем requirements и устанавливаем Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем необходимые директории и файлы
RUN mkdir -p /app/data/index && \
    touch /app/logs/homelab-agent.log && \
    chown -R agent:agent /app

# Переключаемся на пользователя agent
USER agent

# Открываем порт
EXPOSE 8000

# Команда по умолчанию
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
