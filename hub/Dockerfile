FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends docker.io && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY hub/ ./hub/

EXPOSE 9000
CMD ["sh", "-c", "set -e; echo '── ONE-SHOT RESET: alembic downgrade base ──'; alembic -c hub/alembic.ini downgrade base; echo '── alembic upgrade head ──'; alembic -c hub/alembic.ini upgrade head; echo '── alembic current ──'; alembic -c hub/alembic.ini current; echo '── starting hub.server ──'; exec python -m hub.server"]
