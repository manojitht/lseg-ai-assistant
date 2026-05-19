from __future__ import annotations
import logging
from dataclasses import dataclass, field
import pandas as pd
from src import config
from src.guardrails import guardrails
from src.ingestion.document_loader import Document
from src.llm import bedrock_llm, prompt_templates
from src.retrieval.retriever import Retriever
from src.structured import ticket_query
from src.vector_store.faiss_store import FaissStore

logger = logging.getLogger(__name__)

@dataclass
class AssistantResponse:
    answer: str
    source_type: str # "rag" | "structured-data" | "guardrail-rejection"
    citations: list[str] = field(default_factory=list)
    confidence: float | None = None
    anomaly_flagged: bool = False

class Assistant:
    def __init__(self, store: FaissStore, tickets_df: pd.DataFrame) -> None:
        self._retriever  = Retriever(store)
        self._tickets_df = tickets_df

    def ask(self, query: str) -> AssistantResponse:
        query = query.strip()
        logger.info("query received", extra={"query": query[:120]})

        if ticket_query.is_structured_query(query):
            logger.info("routing to structured handler")
            answer = ticket_query.handle(query, self._tickets_df)
            return AssistantResponse(
                answer=answer,
                source_type="structured-data",
            )

        docs, scores = self._retriever.retrieve(query, top_k=config.TOP_K)
        top_score = max(scores) if scores else 0.0
        logger.info("retrieval complete", extra={"top_score": round(top_score, 4), "n_docs": len(docs)})

        if guardrails.check_confidence(scores):
            logger.warning("confidence guardrail triggered", extra={"top_score": top_score})
            return AssistantResponse(
                answer=(
                    "I don't have sufficient information in the available documents "
                    "to answer this question."
                ),
                source_type="guardrail-rejection",
                confidence=round(top_score, 4),
            )

        guard_result = guardrails.check(query, docs, scores)

        prompt = prompt_templates.build_prompt(
            query=query,
            docs=docs,
            anomaly_note=guard_result.anomaly_note,
            domain_note=guard_result.domain_note,
        )
        answer = bedrock_llm.invoke(prompt)
        logger.info("llm response received")

        citations = _build_citations(docs)

        return AssistantResponse(
            answer=answer,
            source_type="rag",
            citations=citations,
            confidence=round(top_score, 4),
            anomaly_flagged=guard_result.anomaly_note != "",
        )


def build_index(docs_dir: str) -> tuple[FaissStore, pd.DataFrame]:
    from src.embeddings import bedrock_embeddings
    from src.ingestion.chunker import build_all_chunks
    from src.ingestion.document_loader import (
        load_sop_documents,
        load_ticket_documents,
        load_tickets_dataframe,
    )

    logger.info("loading documents from %s", docs_dir)
    sop_docs    = load_sop_documents(docs_dir)
    tickets_df  = load_tickets_dataframe(docs_dir)
    ticket_docs = load_ticket_documents(tickets_df)

    all_chunks = build_all_chunks(sop_docs, ticket_docs)
    logger.info("chunking complete: %d chunks", len(all_chunks))

    logger.info("embedding chunks via Bedrock Titan Embeddings v2")
    embeddings = bedrock_embeddings.embed_batch([c.text for c in all_chunks])

    dim   = len(embeddings[0])
    store = FaissStore(dim=dim)
    store.add(all_chunks, embeddings)
    store.save(config.FAISS_INDEX_PATH)
    logger.info("faiss index built: %d vectors (dim=%d)", len(store), dim)

    return store, tickets_df


def load_or_build_index(docs_dir: str) -> tuple[FaissStore, pd.DataFrame]:
    from src.ingestion.document_loader import load_tickets_dataframe

    if FaissStore.exists(config.FAISS_INDEX_PATH):
        logger.info("loading persisted faiss index from %s", config.FAISS_INDEX_PATH)
        store      = FaissStore.load(config.FAISS_INDEX_PATH)
        tickets_df = load_tickets_dataframe(docs_dir)
        return store, tickets_df

    return build_index(docs_dir)


def _build_citations(docs: list[Document]) -> list[str]:
    seen, citations = set(), []
    for doc in docs:
        src = doc.metadata.get("source", "unknown")
        sec = doc.metadata.get("section", "")
        label = f"{src} § {sec}" if sec and sec != "header" else src
        if label not in seen:
            seen.add(label)
            citations.append(label)
    return citations
