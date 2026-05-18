FROM python:3.12-slim

# Install build deps + Node.js 20 (TS SDK for 0G Compute sidecar).
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpq-dev curl ca-certificates gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Shared package
COPY shared/ /shared/
RUN pip install --no-cache-dir -e /shared

# user-server requirements
COPY user-server/requirements.txt /app/user_server_requirements.txt
RUN pip install --no-cache-dir -r /app/user_server_requirements.txt

# Agent (app) requirements — agent subprocesses spawned from user-server share the same env
COPY app/requirements.txt /app/app_requirements.txt
RUN pip install --no-cache-dir -r /app/app_requirements.txt

# App code (for subprocess spawn)
COPY app/ /app/app/
COPY contracts/ /app/contracts/

# Sidecar deps (TS SDK signs per-request headers for 0G Compute)
WORKDIR /app/app/llm/sidecar
RUN npm install --omit=dev

# User-server code
WORKDIR /app
COPY user-server/user_server/ /app/user_server/
COPY user-server/alembic/ /app/alembic/
COPY user-server/alembic.ini /app/alembic.ini

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && python -m user_server.server"]
