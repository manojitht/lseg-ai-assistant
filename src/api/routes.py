from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException, Request
from src.api.schemas import AskRequest, AskResponse, HealthResponse
from src.llm.bedrock_llm import RateLimitError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["ops"])
def health(request: Request) -> HealthResponse:
    store = request.app.state.store
    return HealthResponse(
        status="ok",
        index_loaded=store is not None,
        index_size=len(store) if store else 0,
    )


@router.post("/ask", response_model=AskResponse, tags=["assistant"])
def ask(body: AskRequest, request: Request) -> AskResponse:
    assistant = request.app.state.assistant
    if assistant is None:
        raise HTTPException(status_code=503, detail="Assistant not initialised yet.")

    logger.info("POST /ask query=%r", body.query[:80])
    try:
        response = assistant.ask(body.query)
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))

    return AskResponse(
        answer=response.answer,
        source_type=response.source_type,
        citations=response.citations,
        confidence=response.confidence,
        anomaly_flagged=response.anomaly_flagged,
    )
