import json
from fastapi import APIRouter, Depends, HTTPException
from logging import Logger

from app.domain.schemas import ChatRequest, ChatResponse
from app.controllers.dependencies import get_debate_service, get_logger
from app.services.chat import DebateService
from app.core.metrics import CHAT_REQUESTS, CHAT_PAYLOAD_BYTES, CHAT_RESPONSE_CHARS
from app.domain.errors import NotFoundError 

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
        last = ""
        if resp.message:
            last_item = resp.message[-1]
            if hasattr(last_item, "message"):
                last = last_item.message or ""
            elif isinstance(last_item, dict):
                last = last_item.get("message") or last_item.get("content", "") or ""

        CHAT_RESPONSE_CHARS.observe(len(last))
        CHAT_REQUESTS.labels(status="ok").inc()
        logger.info("POST /chat response last=%s", last[:120])
        return resp
    except NotFoundError as e:
        CHAT_REQUESTS.labels(status="not_found").inc()
        logger.warning("POST /chat 404: %s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        CHAT_REQUESTS.labels(status="error").inc()
        logger.exception("POST /chat failed: %s", e)
        raise
