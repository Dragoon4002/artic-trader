FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends docker.io && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY hub/ ./hub/

EXPOSE 9000
CMD ["sh", "-c", "set -e; alembic -c hub/alembic.ini upgrade head; python -m hub.scripts.diagnose_db; exec python -m hub.server"]
