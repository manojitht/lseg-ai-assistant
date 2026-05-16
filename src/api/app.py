"""
FastAPI application factory with lifespan index loading.

On startup:
  - Load (or build) the FAISS index from docs/
  - Initialise the Assistant
  - Attach both to app.state so routes can access them via request.app.state

This ensures embeddings are computed once and reused across all requests.
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.assistant import Assistant, load_or_build_index


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src import config
    logger.info("starting up — region=%s model=%s", config.BEDROCK_REGION, config.LLM_MODEL_ID)
    store, tickets_df = load_or_build_index(config.DOCS_DIR)
    app.state.store     = store
    app.state.assistant = Assistant(store=store, tickets_df=tickets_df)
    logger.info("assistant ready — %d vectors indexed", len(store))
    yield
    logger.info("shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="LSEG DSM AI Assistant",
        description=(
            "Internal AI assistant for LSEG DSM operational workflows. "
            "Answers questions over SOP documents and incident tickets using "
            "Amazon Bedrock (RAG) with deterministic structured query support."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()
