import uuid
from typing import Iterable
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.domain import models


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, topic: str, stance: str) -> models.Conversation:
        cid = uuid.uuid4().hex
        conv = models.Conversation(id=cid, topic=topic, stance=stance)
        self.db.add(conv)
        self.db.flush()

        return conv

    def get(self, conversation_id=str) -> models.Conversation | None:
        return self.db.get(models.Conversation, conversation_id)


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, conversation: models.Conversation, role: str, content: str) -> models.Message:
        msg = models.Message(conversation_id=conversation.id, role=role, content=content)
        self.db.add(msg)
        self.db.flush()

        return msg

    def last_n(self, conversation_id: str, n: int = 10) -> Iterable[models.Message]:
        stmt = select(models.Message).where(models.Message.conversation_id == conversation_id).order_by(
            models.Message.id.desc()).limit(n)

        return list(reversed(self.db.scalars(stmt).all()))
