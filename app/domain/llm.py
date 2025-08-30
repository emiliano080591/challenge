from typing import Protocol
from app.domain import models


class DebateLLM(Protocol):
    def reply(self, *, topic: str, stance: str, history: list[models.Message]) -> str: ...
