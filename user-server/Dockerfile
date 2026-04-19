FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Shared package first so layer caches while user-server code churns.
COPY shared/ /shared/
RUN pip install --no-cache-dir -e /shared

COPY user-server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY user-server/ /app/

EXPOSE 8000
CMD ["python", "-m", "user_server.server"]
