FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends docker.io && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY hub/ ./hub/

EXPOSE 9000
CMD ["sh", "-c", "set -e; echo '── ONE-SHOT RESET: drop schema public ──'; python -c \"import os, psycopg2; u=os.environ['DATABASE_URL']; u=u.replace('postgres://','postgresql://').split('?')[0]; c=psycopg2.connect(u, sslmode='require'); c.autocommit=True; cur=c.cursor(); cur.execute('DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;'); print('schema dropped + recreated'); c.close()\"; echo '── alembic upgrade head ──'; alembic -c hub/alembic.ini upgrade head; echo '── alembic current ──'; alembic -c hub/alembic.ini current; echo '── starting hub.server ──'; exec python -m hub.server"]
