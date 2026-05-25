FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    bash \
    ca-certificates \
    git \
    docker.io \
    docker-compose \
    netcat-openbsd \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash agent && usermod -aG docker agent

# Официальный headless Cursor CLI → ~/.local/bin/agent
# https://cursor.com/docs/cli/installation
USER agent
ENV HOME=/home/agent
ENV PATH="/home/agent/.local/bin:${PATH}"
RUN curl https://cursor.com/install -fsS | bash \
    && test -x /home/agent/.local/bin/agent \
    && /home/agent/.local/bin/agent --version

USER root
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data/index /app/logs/incidents /app/github-config \
    /home/agent/.cursor \
    && touch /app/logs/homelab-agent.log \
    && chown -R agent:agent /app /home/agent/.cursor

USER agent
ENV CURSOR_CLI_PATH=/home/agent/.local/bin/agent
ENV CURSOR_WORKSPACE=/app/homelab
ENV CURSOR_AGENT_MODE=ask
ENV CURSOR_TELEGRAM_MAX_CHARS=1400
ENV CURSOR_INCIDENTS_DIR=/app/logs/incidents

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=3 \
    CMD /home/agent/.local/bin/agent --version && curl -f http://localhost:8000/api/webhook/uptime-kuma/health

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
