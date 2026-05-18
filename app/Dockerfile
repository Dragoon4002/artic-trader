FROM python:3.12-slim

# Install Node.js 20 (TS SDK for 0G Compute) + minimal build deps.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY contracts/ ./contracts/

# Install Node deps for 0G Compute sidecar (TS SDK signs per-request headers).
WORKDIR /app/app/llm/sidecar
RUN npm install --omit=dev

WORKDIR /app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
