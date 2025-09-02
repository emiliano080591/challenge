COMPOSE_FILE=docker-compose.yml

.PHONY: help up down rebuild logs ps clean test

help:
	@echo "Comandos disponibles:"
	@echo "  make up       -> Levanta todos los servicios en segundo plano"
	@echo "  make down     -> Baja todos los servicios"
	@echo "  make rebuild  -> Reconstruye imágenes y levanta servicios"
	@echo "  make logs     -> Muestra logs en vivo de todos los servicios"
	@echo "  make ps       -> Muestra estado de los servicios"
	@echo "  make clean    -> Baja servicios y borra volúmenes (⚠️ datos de DB y Grafana se pierden)"
	@echo "  make test     -> Ejecuta los tests con pytest"

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
	docker compose -f $(COMPOSE_FILE) run --rm api pytest -vv --maxfail=1 --disable-warnings -q
