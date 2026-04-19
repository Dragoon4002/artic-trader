.PHONY: dev down migrate openapi e2e-smoke test

COMPOSE := docker compose -f docker-compose.dev.yml --env-file .env.dev

dev:
	@test -f .env.dev || (echo "create .env.dev from .env.dev.example first" && exit 1)
	$(COMPOSE) up -d
	@echo "waiting for hub /health..."
	@until curl -fs localhost:9000/health >/dev/null 2>&1; do sleep 1; done
	@echo "waiting for user-server /health..."
	@until curl -fs localhost:9100/health >/dev/null 2>&1; do sleep 1; done
	@echo "dev stack ready."

down:
	$(COMPOSE) down

migrate:
	alembic -c hub/alembic.ini upgrade head
	alembic -c user-server/alembic.ini upgrade head

openapi:
	PYTHONPATH=. python scripts/dump_openapi.py > openapi.yaml
	@echo "wrote openapi.yaml"

e2e-smoke:
	curl -fs localhost:9000/health >/dev/null && echo "hub OK"
	curl -fs localhost:9100/health >/dev/null && echo "user-server OK"

test:
	pytest shared/tests tests
