# Debate Bot (FastAPI · Clean Architecture)

API de chatbot “debates” que sostiene su postura y busca persuadir, con memoria corta por conversación y observabilidad lista (Prometheus + Grafana).

---
## Requisitos
- Python 3.12 (para correr local)
- Docker & Docker Compose (para stack completo con DB(`postgres`) + observabilidad)
- Clave de OpenAI (modelo sugerido: `gpt-4o-mini`)

---

## 1) Configurar variables de entorno
Crea un archivo `.env` en la raíz del proyecto:
```env
# App
ENV=dev
LOG_LEVEL=DEBUG
API_PREFIX=/api

# DB local (para correr fuera de Docker)
DATABASE_URL=sqlite+pysqlite:///./local.db

# OpenAI
OPENAI_API_KEY=sk-...tu_clave...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=350

```

> En Docker, el `docker-compose.yml` ya sobrescribe `DATABASE_URL` a Postgres dentro del contenedor de la API. 
> En local usarás SQLite por defecto.

---

## Correr en local(sin Docker)
Instala dependencias y levanta la app:
```bash
python -m venv .venv
source .venv/bin/activate          # (en Windows: .venv\Scripts\activate)
pip install --upgrade pip
pip install -r requirements.txt

# arranque local
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints útiles:
- Health: http://127.0.0.1:8000/healthz
- Docs Swagger: http://127.0.0.1:8000/docs

---
## 3) Correr con Docker Compose (stack unificado)
El archivo `docker-compose.yml` ya define: **api + postgres + prometheus + grafana.**

Con el Makefile:
```bash
make rebuild   # reconstruye imágenes y levanta todo
make ps        # estado de servicios
make logs      # logs en vivo
make down      # baja servicios
make clean     # baja y elimina volúmenes (resetea DB y Grafana)

```

Manual, si prefieres:
```bash
docker compose up -d --build
```
Endpoints:
- API: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

> En Prometheus (UI) ve a **Status → Targets** y confirma que `kopi-api` esté UP.

---

## 4) Probar el chatbot con curl
### Iniciar una conversación (sin `conversation_id`)
```bash
curl -s http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": null, "message": "Topic: Espacio; Stance: El hombre nunca llego a la luna"}' | jq

```
### Continuar la conversación
```bash
CID="pegAQUI_tu_conversation_id"
curl -s http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"conversation_id\": \"${CID}\", \"message\": \"No me convences, dame evidencia concreta\"}" | jq

```
> El servicio mantiene una “memoria corta”: últimos 5 mensajes por rol.

---

## 5) Endpoints
* `GET /healthz` — liveness.
* `POST /api/chat` — cuerpo:
```json
{ "conversation_id": null, "message": "Topic: Espacio; Stance: El hombre nunca llego a la luna" }
```
o para continuar:
```json
{ "conversation_id": "ID_DEVUELTO", "message": "Sigo sin estar convencido" }
```
* `GET /metrics` — métricas Prometheus (Prometheus las scrapea, no es para consumo humano).

---

## 6) Documentación de la aplicación

La documentación técnica de Debate Bot se sirve con Docsify
, que convierte archivos Markdown en un sitio estático.

Cómo acceder
* Local con Docker Compose (puerto 3001):
```arduino
http://localhost:3001
```
* Homepage: sección Arquitectura, con:
  - Diagrama de Componentes (Excalidraw).
  - Diagrama de Secuencia de /chat (PlantUML).
  - ADR-0001 con decisiones de arquitectura.

![doc](docs/images/docsify.png)
--- 

