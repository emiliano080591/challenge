import os
import pytest
from typing import Generator
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.domain import models  # noqa: F401
from app.infrastructure.db import Base, get_db
from app.controllers import chat as chat_router
from app.services.chat import DebateService

os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("OPENAI_MODEL", "gpt-4o-mini")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

@pytest.fixture(scope="function")
def engine_mem():
    eng = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        eng.dispose()

@pytest.fixture(scope="function")
def db_session(engine_mem) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(bind=engine_mem, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


class StubLLMOk:
    def reply(self, topic: str, stance: str, history):
        h = list(history)
        return f"RESPUESTA_MOCK [topic={topic} stance={stance} hist={len(h)}]"

class StubLLMFail:
    def reply(self, topic: str, stance: str, history):
        raise RuntimeError("LLM down")

@pytest.fixture
def stub_llm_ok():
    return StubLLMOk()

@pytest.fixture
def stub_llm_fail():
    return StubLLMFail()

@pytest.fixture(scope="function")
def test_app(db_session: Session, stub_llm_ok) -> FastAPI:
    app = FastAPI()
    app.include_router(chat_router.router, prefix="/api")

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _override_get_db

    try:
        from app.controllers.dependencies import get_debate_service
        def _override_service(db: Session = Depends(_override_get_db)) -> DebateService:
            return DebateService(db=db, llm=stub_llm_ok)
        app.dependency_overrides[get_debate_service] = _override_service
    except ImportError:
        pass

    return app

@pytest.fixture(scope="function")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)
