FROM python:3.12-slim

RUN pip install --no-cache-dir httpx==0.27.*

WORKDIR /app
COPY agent.py .

EXPOSE 8080

CMD ["python", "agent.py"]
