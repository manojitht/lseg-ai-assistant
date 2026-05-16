"""
Prompt templates with explicit system / user separation.

System prompt defines strict rules — the LLM must cite sources, refuse when
context is insufficient, and flag policy anomalies. Temperature=0 enforces
deterministic, compliance-grade output.
"""
from __future__ import annotations

from src.ingestion.document_loader import Document

SYSTEM_PROMPT = """You are an internal AI assistant for LSEG DSM (Data & Analytics) operations.
Your sole purpose is to answer operational questions using ONLY the context provided below.

STRICT RULES — follow every one without exception:
1. CITE EVERY SOURCE using the format [SOURCE: <name>] immediately after the relevant statement.
   Examples: [SOURCE: SOP-001 § MFA Reset Policy]  [SOURCE: TKT-1142]
2. If the provided context does not contain enough information to answer, respond with exactly:
   "I don't have sufficient information in the available documents to answer this question."
   Do NOT guess, infer, or use any external knowledge.
3. Clearly state whether your answer is derived from:
   - A policy document (SOP) — prefix with "According to policy:"
   - Incident ticket data — prefix with "Based on ticket data:"
4. If a POLICY ANOMALY flag appears in the context, you MUST explicitly:
   a) State that a policy violation has been detected.
   b) Quote the correct policy from the SOP.
   c) Refuse to advise any action that violates the policy.
5. Never hallucinate ticket IDs, SOP sections, or procedural steps.
6. Keep answers concise and actionable."""


def build_prompt(
    query: str,
    docs: list[Document],
    anomaly_note: str = "",
    domain_note: str = "",
) -> dict:
    """
    Build the system + user prompt dict in Claude Messages API format.
    Returns {"system": str, "messages": [{"role": "user", "content": str}]}
    """
    context_blocks = _build_context(docs)
    user_content   = _build_user_content(query, context_blocks, anomaly_note, domain_note)
    return {
        "system":   SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_content}],
    }



def _build_context(docs: list[Document]) -> str:
    blocks = []
    for i, doc in enumerate(docs, start=1):
        source = _format_source(doc)
        blocks.append(f"[{i}] SOURCE: {source}\n{doc.text.strip()}")
    return "\n\n---\n\n".join(blocks)


def _format_source(doc: Document) -> str:
    meta = doc.metadata
    src  = meta.get("source", "unknown")
    sec  = meta.get("section", "")
    if sec and sec != "header":
        return f"{src} § {sec}"
    return src


def _build_user_content(
    query: str,
    context: str,
    anomaly_note: str,
    domain_note: str,
) -> str:
    parts = []

    if anomaly_note:
        parts.append(f"⚠ POLICY ANOMALY FLAG:\n{anomaly_note}\n")

    if domain_note:
        parts.append(f"ℹ RETRIEVAL NOTE:\n{domain_note}\n")

    parts.append(f"CONTEXT:\n{context}")
    parts.append(f"QUESTION:\n{query}")
    parts.append("ANSWER (with source citations):")

    return "\n\n".join(parts)
