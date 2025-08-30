from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from logging import Logger

from app.infrastructure.db import get_db
from app.infrastructure.logging import logger
from app.services.chat import DebateService

DBSession = Annotated[Session, Depends(get_db)]


def get_logger() -> Logger:
    return logger


def get_debate_service(db: DBSession) -> DebateService:
    return DebateService(db)
