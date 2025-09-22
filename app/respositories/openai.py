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
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS

    def reply(self, topic: str, stance: str, history: List[models.Message]) -> str:
        messages = [
            {"role": "system", "content": f"""Eres un bot de debate profesional...
Defiendes SIEMPRE: "{stance}" sobre "{topic}"...
(etc)
""".strip()}
        ]
        for m in history:
            role = "assistant" if m.role == "bot" else "user"
            messages.append({"role": role, "content": m.content})

        with Timer() as t:
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                OPENAI_REQUESTS.labels(status="ok", error_type="").inc()

                usage = getattr(resp, "usage", None)
                if usage:
                    OPENAI_TOKENS.labels(kind="prompt").inc(getattr(usage, "prompt_tokens", 0) or 0)
                    OPENAI_TOKENS.labels(kind="completion").inc(getattr(usage, "completion_tokens", 0) or 0)
                    OPENAI_TOKENS.labels(kind="total").inc(getattr(usage, "total_tokens", 0) or 0)

                return resp.choices[0].message.content.strip()

            except (RateLimitError, APIConnectionError, APIError) as e:
                OPENAI_REQUESTS.labels(status="error", error_type=type(e).__name__).inc()
                logger.exception("OpenAI error: %s", e)
                raise
            except Exception as e:
                OPENAI_REQUESTS.labels(status="error", error_type=type(e).__name__).inc()
                logger.exception("OpenAI unexpected error: %s", e)
                raise
            finally:
                if getattr(t, "elapsed", None) is not None:
                    OPENAI_LATENCY.observe(t.elapsed)
