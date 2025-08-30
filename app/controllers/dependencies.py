from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from logging import Logger

from app.infrastructure.db import get_db
from app.infrastructure.logging import logger
from app.respositories.openai import OpenAIDebateLLM
from app.services.chat import DebateService

DBSession = Annotated[Session, Depends(get_db)]


def get_logger() -> Logger:
    return logger


def get_debate_llm() -> OpenAIDebateLLM:
    return OpenAIDebateLLM()


def get_debate_service(db: DBSession, llm: OpenAIDebateLLM = Depends(get_debate_llm)) -> DebateService:
    return DebateService(db=db, llm=llm)
