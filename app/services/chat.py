from typing import List, Tuple
from sqlalchemy.orm import Session
from openai import OpenAI

from app.respositories.sql import ConversationRepository, MessageRepository
from app.domain.schemas import ChatRequest, ChatResponse
from app.domain import models
from app.core.config import settings
from app.infrastructure.logging import logger


class DebateService:
    """
    Debate service backed by OpenAI Chat Completions.
    - Bloquea postura vía prompt 'system' por conversación
    - Memoria corta: últimos 5 de usuario + 5 del bot
    - Respuestas persuasivas y enfocadas en el tema
    """

    def __init__(self, db: Session):
        self.db = db
        self.convs = ConversationRepository(db)
        self.msgs = MessageRepository(db)
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _parse_topic_and_stance(self, first_message: str) -> Tuple[str, str]:
        """
        Soporta formato 'Topic: X; Stance: Y'.
        Fallback: topic = texto; stance = después de 'that' si existe.
        """
        text = (first_message or "").strip()
        topic, stance = "general debate", "bot's position"
        if ";" in text and ":" in text:
            try:
                parts = {
                    k.strip().lower(): v.strip()
                    for k, v in (seg.split(":", 1) for seg in text.split(";"))
                }
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

    def _system_prompt(self, topic: str, stance: str) -> str:
        return f"""
            Eres un bot de debate profesional.
            Defiendes SIEMPRE esta postura, sin ceder: "{stance}" sobre el tema "{topic}".
            Eres persuasivo, respetuoso y focalizado. Evita ataques personales y mantén coherencia.
            Usa variedad de tácticas: evidencia observable, preguntas socráticas, consecuencias, reframing y analogías.
            Cierra cada respuesta con una pregunta breve que impulse el diálogo.
            
            Estructura interna (no la muestres):
            1) Borrador (3–6 frases)
            2) Auto-crítica (1–2 líneas)
            3) Versión revisada (respuesta final)
            
            Entrega ÚNICAMENTE la versión revisada.
            """.strip()

    def _build_messages(self, conv: models.Conversation, history: List[models.Message]):
        # Limitar a 5 por rol y mantener orden cronológico
        users = [m for m in history if m.role == "user"][-5:]
        bots = [m for m in history if m.role == "bot"][-5:]
        merged = sorted(users + bots, key=lambda m: m.id)

        messages = [{"role": "system", "content": self._system_prompt(conv.topic, conv.stance)}]
        for m in merged:
            role = "assistant" if m.role == "bot" else "user"
            messages.append({"role": role, "content": m.content})
        return messages

    def _llm_reply(self, conv: models.Conversation, history: list[models.Message]) -> str:
        messages = self._build_messages(conv, history)
        logger.debug("Mensajes enviados a OpenAI: %s", messages)

        try:
            resp = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=350,
            )
            reply = resp.choices[0].message.content.strip()
            logger.debug("Respuesta OpenAI: %s", reply)
            return reply
        except Exception as e:
            logger.exception("Fallo llamada a OpenAI: %s", e)
            return "No puedo responder en este momento, pero sigo defendiendo mi postura."

    def handle(self, payload: ChatRequest) -> ChatResponse:
        logger.info("Nueva request: %s", payload.dict())

        if not payload.conversation_id:
            topic, stance = self._parse_topic_and_stance(payload.message)
            logger.debug("Creando nueva conversación topic=%s stance=%s", topic, stance)
            conv = self.convs.create(topic=topic, stance=stance)
        else:
            conv = self.convs.get(payload.conversation_id)
            if not conv:
                topic, stance = self._parse_topic_and_stance(payload.message)
                logger.warning("Conversation %s no encontrada, creando nueva", payload.conversation_id)
                conv = self.convs.create(topic=topic, stance=stance)

        self.msgs.add(conv, role="user", content=payload.message)
        history = self.msgs.last_n(conv.id, n=10)
        logger.debug("Historial cargado: %s mensajes", len(history))

        try:
            reply = self._llm_reply(conv, history)
        except Exception as e:
            logger.exception("Error en _llm_reply: %s", e)
            reply = "⚠️ Error al generar respuesta, mantengo mi postura."

        self.msgs.add(conv, role="bot", content=reply)

        recent = self.msgs.last_n(conv.id, n=10)
        logger.info("Respuesta generada: %s", reply[:100])  # muestra primeros 100 chars

        return ChatResponse(
            conversation_id=conv.id,
            message=[{"role": m.role, "content": m.content} for m in recent]
        )
