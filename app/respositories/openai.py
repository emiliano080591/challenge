from __future__ import annotations
from typing import List
from openai import OpenAI, APIConnectionError, APIError, RateLimitError
from app.core.config import settings
from app.domain import models
from app.infrastructure.logging import logger
from app.core.metrics import OPENAI_REQUESTS, OPENAI_LATENCY, OPENAI_TOKENS, Timer


class OpenAIDebateLLM:
    def __init__(self, client: OpenAI | None = None):
        self.client = client or OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.temperature = getattr(settings, "OPENAI_TEMPERATURE", 0.3)
        self.max_tokens = getattr(settings, "OPENAI_MAX_TOKENS", 350)

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

    def reply(self, *, topic: str, stance: str, history: List[models.Message]) -> str:
        messages = self._pack_messages(topic=topic, stance=stance, history=history)
        logger.debug("OpenAI payload msgs=%d", len(messages))
        try:
            with Timer() as t:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            OPENAI_LATENCY.observe(t.elapsed)
            OPENAI_REQUESTS.labels(status="ok", error_type="").inc()

            choice = resp.choices[0]
            text = (choice.message.content or "").strip()

            # Si el SDK retorna usage, regístralo
            usage = getattr(resp, "usage", None)
            if usage:
                if getattr(usage, "prompt_tokens", None) is not None:
                    OPENAI_TOKENS.labels(kind="prompt").inc(usage.prompt_tokens)
                if getattr(usage, "completion_tokens", None) is not None:
                    OPENAI_TOKENS.labels(kind="completion").inc(usage.completion_tokens)
                if getattr(usage, "total_tokens", None) is not None:
                    OPENAI_TOKENS.labels(kind="total").inc(usage.total_tokens)

            return text

        except RateLimitError as e:
            OPENAI_REQUESTS.labels(status="error", error_type="rate_limit").inc()
            logger.exception("OpenAI rate limit")
        except APIConnectionError as e:
            OPENAI_REQUESTS.labels(status="error", error_type="conn").inc()
            logger.exception("OpenAI connection error")
        except APIError as e:
            OPENAI_REQUESTS.labels(status="error", error_type="api").inc()
            logger.exception("OpenAI API error")
        except Exception as e:
            OPENAI_REQUESTS.labels(status="error", error_type="unexpected").inc()
            logger.exception("OpenAI unexpected error")

        return ("Mantengo mi postura. No puedo responder ahora por un problema temporal, "
                "pero sigamos con los argumentos ya planteados. ¿Qué parte cuestionas más?")
