from __future__ import annotations
from typing import List
from openai import OpenAI, APIConnectionError, APIError, RateLimitError
from app.core.config import settings
from app.domain import models
from app.infrastructure.logging import logger


class OpenAIDebateLLM:
    def __init__(self, client: OpenAI | None = None):
        self.client = client or OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.temperature = getattr(settings, "OPENAI_TEMPERATURE", 0.3)
        self.max_tokens = getattr(settings, "OPENAI_MAX_TOKENS", 350)

    # ==== prompt y armado de mensajes ====
    def _system_prompt(self, topic: str, stance: str) -> str:
        return f"""
            Eres un bot de debate profesional.
            Defiendes SIEMPRE esta postura, sin ceder: "{stance}" sobre el tema "{topic}".
            Eres persuasivo, respetuoso y focalizado; evita ataques personales.
            Usa evidencia, preguntas socráticas, consecuencias, reframing y analogías.
            Cierra con una pregunta breve que impulse el diálogo.
            
            Estructura interna (no la muestres):
            1) Borrador (3–6 frases)
            2) Auto-crítica (1–2 líneas)
            3) Versión revisada (respuesta final)
            
            Entrega ÚNICAMENTE la versión revisada.
            """.strip()

    def _pack_messages(self, *, topic: str, stance: str, history: List[models.Message]):
        users = [m for m in history if m.role == "user"][-5:]
        bots = [m for m in history if m.role == "bot"][-5:]
        merged = sorted(users + bots, key=lambda m: m.id)

        messages = [{"role": "system", "content": self._system_prompt(topic, stance)}]
        for m in merged:
            role = "assistant" if m.role == "bot" else "user"
            messages.append({"role": role, "content": m.content})
        return messages

    # ==== Único método público ====
    def reply(self, *, topic: str, stance: str, history: List[models.Message]) -> str:
        messages = self._pack_messages(topic=topic, stance=stance, history=history)
        logger.debug("OpenAI payload msgs=%d", len(messages))
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            text = (resp.choices[0].message.content or "").strip()
            logger.debug("OpenAI reply(len=%d)", len(text))
            return text
        except (RateLimitError, APIConnectionError, APIError) as e:
            logger.exception("OpenAI error: %s", e)
            return ("Mantengo mi postura. No puedo ampliar ahora por un problema temporal, "
                    "pero avancemos con los argumentos ya planteados. ¿Qué parte cuestionas más?")
        except Exception as e:
            logger.exception("OpenAI unexpected error: %s", e)
            return ("Mantengo mi postura. No puedo responder en este momento, "
                    "pero puedo reformular el argumento. ¿Qué punto quieres discutir?")
