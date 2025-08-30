from fastapi import FastAPI
from app.core.config import settings
from app.core.metrics import setup_metrics
from app.core.middleware import RequestIDLogMiddleware
from app.infrastructure.db import Base, engine
from app.domain import models

from app.controllers import chat as chat_router

app = FastAPI(title="Kopi Debate Bot", version="0.1.0")

Base.metadata.create_all(bind=engine)

app.add_middleware(RequestIDLogMiddleware)
app.include_router(chat_router.router, prefix=settings.API_PREFIX)

setup_metrics(app)


@app.get("/healthz", tags=["meta"], summary="Liveness probe")
async def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
