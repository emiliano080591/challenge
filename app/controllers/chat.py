from fastapi import APIRouter, Depends
from logging import Logger

from app.domain.schemas import ChatRequest, ChatResponse
from app.controllers.dependencies import get_debate_service, get_logger
from app.services.chat import DebateService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse, summary="Debate reply")
async def debate(
        payload: ChatRequest,
        service: DebateService = Depends(get_debate_service),
        logger: Logger = Depends(get_logger),
) -> ChatResponse:
    logger.info("POST /chat payload=%s", payload.model_dump())
    resp = service.handle(payload)
    last = resp.message[-1].message if resp.message else ""
    logger.info("POST /chat response last=%s", last[:120])
    return resp
