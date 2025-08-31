# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencias
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Código
COPY app /app/app
COPY alembic /app/alembic
COPY .env ./

RUN useradd -m appuser
USER appuser

EXPOSE 8000

# Arranque (uvicorn directo; puedes cambiar a gunicorn+uvicorn workers si quieres)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
