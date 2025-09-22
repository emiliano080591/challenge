COMPOSE_FILE=docker-compose.yml

# --- Python local (venv) ---
VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: help install run up down rebuild logs ps clean test test-local venv

help:
	@echo "Comandos disponibles:"
	@echo "  make venv        -> Crea venv local (.venv) si no existe"
	@echo "  make install     -> Instala dependencias en el venv local"
	@echo "  make run         -> Ejecuta la API local (uvicorn) con el venv"
	@echo "  make up          -> Levanta servicios (Docker)"
	@echo "  make down        -> Baja servicios (Docker)"
	@echo "  make rebuild     -> Reconstruye imágenes y levanta (Docker)"
	@echo "  make logs        -> Logs en vivo (Docker)"
	@echo "  make ps          -> Estado de servicios (Docker)"
	@echo "  make clean       -> Baja y borra volúmenes (Docker)"
	@echo "  make test        -> Ejecuta tests dentro del contenedor 'api' montando ./tests"
	@echo "  make test-local  -> Ejecuta tests en el entorno local (venv)"

venv:
	test -d $(VENV) || python3 -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run: install
	$(PY) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

up:
	docker compose -f $(COMPOSE_FILE) up -d

down:
	docker compose -f $(COMPOSE_FILE) down

rebuild:
	docker compose -f $(COMPOSE_FILE) up -d --build

logs:
	docker compose -f $(COMPOSE_FILE) logs -f

ps:
	docker compose -f $(COMPOSE_FILE) ps

clean:
	docker compose -f $(COMPOSE_FILE) down -v

test:
	docker compose -f $(COMPOSE_FILE) run --rm \
		-e OPENAI_API_KEY=dummy \
		-v $$PWD/tests:/app/tests \
		api pytest tests -vv --maxfail=1 --disable-warnings

