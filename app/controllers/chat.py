import json
from fastapi import APIRouter, Depends
from logging import Logger

from app.domain.schemas import ChatRequest, ChatResponse
from app.controllers.dependencies import get_debate_service, get_logger
from app.services.chat import DebateService
from app.core.metrics import CHAT_REQUESTS, CHAT_PAYLOAD_BYTES, CHAT_RESPONSE_CHARS

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse, summary="Debate reply")
async def debate(
        payload: ChatRequest,
        service: DebateService = Depends(get_debate_service),
        logger: Logger = Depends(get_logger),
) -> ChatResponse:
    try:
        in_bytes = len(json.dumps(payload.model_dump(), ensure_ascii=False).encode("utf-8"))
        CHAT_PAYLOAD_BYTES.observe(in_bytes)
    except Exception:
        pass
    logger.info("POST /chat payload=%s", payload.model_dump())

    try:
        resp = service.handle(payload)
        last = resp.message[-1].message if resp.message else ""
        CHAT_RESPONSE_CHARS.observe(len(last))
        CHAT_REQUESTS.labels(status="ok").inc()
        logger.info("POST /chat response last=%s", last[:120])

        return resp
    except Exception as e:
        CHAT_REQUESTS.labels(status="error").inc()
        logger.exception("POST /chat failed: %s", e)
        raise
