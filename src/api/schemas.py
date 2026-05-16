from __future__ import annotations
from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000, description="The operational question to ask")

class AskResponse(BaseModel):
    answer: str = Field(..., description="The assistant's answer")
    source_type: str = Field(
        ...,
        description=(
            "'rag' — answer from retrieved documents via LLM; "
            "'structured-data' — deterministic pandas query; "
            "'guardrail-rejection' — refused due to low confidence"
        ),
    )
    citations: list[str] = Field(
        default_factory=list,
        description="Source references cited in the answer (SOP sections or ticket IDs)",
    )
    confidence: float | None = Field(
        default=None,
        description="Top cosine similarity score from retrieval (None for structured queries)",
    )
    anomaly_flagged: bool = Field(
        default=False,
        description="True if a policy anomaly (e.g. social-engineering pattern) was detected",
    )


class HealthResponse(BaseModel):
    status: str = Field(..., description="'ok' when the service is ready")
    index_loaded: bool = Field(..., description="True when the FAISS index is in memory")
    index_size: int = Field(..., description="Number of vectors in the index")
