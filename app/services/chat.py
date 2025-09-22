from typing import Tuple
from sqlalchemy.orm import Session

from app.domain.schemas import ChatRequest, ChatResponse
from app.respositories.sql import ConversationRepository, MessageRepository
from app.domain.llm import DebateLLM
from app.infrastructure.logging import logger
from app.core.metrics import CONVERSATIONS_STARTED, MESSAGES_TOTAL
from app.domain.errors import NotFoundError  # <---

class DebateService:
    def __init__(self, db: Session, llm: DebateLLM):
        self.db = db
        self.convs = ConversationRepository(db)
        self.msgs = MessageRepository(db)
        self.llm = llm

    def _parse_topic_and_stance(self, first_message: str) -> Tuple[str, str]:
        text = (first_message or "").strip()
        topic, stance = "general debate", "bot's position"
        if ";" in text and ":" in text:
            try:
                parts = {k.strip().lower(): v.strip() for k, v in (seg.split(":", 1) for seg in text.split(";"))}
                topic = parts.get("topic", topic)
                stance = parts.get("stance", stance)
            except ValueError:
                pass
        else:
            topic = text[:128] or topic
            low = text.lower()
            if "that" in low:
                stance = text[low.find("that") + 4:].strip()[:128] or stance
        return topic, stance

    def handle(self, payload: ChatRequest) -> ChatResponse:
        logger.info("Nueva request: %s", payload.model_dump())

        if payload.conversation_id:
            conv = self.convs.get(payload.conversation_id)
            if not conv:
                raise NotFoundError(f"Conversation {payload.conversation_id} not found")
        else:
            topic, stance = self._parse_topic_and_stance(payload.message)
            logger.debug("Creando conversación topic=%s stance=%s", topic, stance)
            conv = self.convs.create(topic=topic, stance=stance)
            CONVERSATIONS_STARTED.inc()

        self.msgs.add(conv, role="user", content=payload.message)
        MESSAGES_TOTAL.labels(role="user").inc()

        history = self.msgs.last_n(conv.id, n=10)
        logger.debug("Historial antes de LLM: %d", len(history))

        reply = self.llm.reply(topic=conv.topic, stance=conv.stance, history=history)
        logger.debug("LLM respuesta previa: %s", reply[:120])

        self.msgs.add(conv, role="bot", content=reply)
        MESSAGES_TOTAL.labels(role="bot").inc()

        recent = self.msgs.last_n(conv.id, n=10)
        logger.info("Respuesta generada (len=%d)", len(reply))

        return ChatResponse(
            conversation_id=conv.id,
            message=[{"role": m.role, "message": m.content} for m in recent]
        )
