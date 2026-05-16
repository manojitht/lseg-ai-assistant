from __future__ import annotations

import re
from src.ingestion.document_loader import Document


def chunk_sop(doc: Document) -> list[Document]:
    """
    Split an SOP document on ## headers — one chunk per section.
    Each chunk inherits the parent source and gains a 'section' metadata key.

    Section-level chunking is intentional: SOP sections are atomic procedures
    whose numbered steps must stay together to preserve execution order.
    """
    text  = doc.text
    parts = re.split(r"(?m)^##\s+", text)

    # parts[0] is the preamble (title, version, classification)
    chunks: list[Document] = []

    # Keep preamble as its own chunk (contains version/classification metadata)
    if parts[0].strip():
        chunks.append(Document(
            text=parts[0].strip(),
            metadata={**doc.metadata, "section": "header", "doc_type": "sop"},
        ))

    for part in parts[1:]:
        lines   = part.strip().splitlines()
        heading = lines[0].strip() if lines else "unknown"
        body    = "\n".join(lines[1:]).strip()
        chunk_text = f"## {heading}\n\n{body}"
        chunks.append(Document(
            text=chunk_text,
            metadata={**doc.metadata, "section": heading, "doc_type": "sop"},
        ))

    return chunks


def chunk_tickets(ticket_docs: list[Document]) -> list[Document]:
    """Each ticket row is already a self-contained chunk; stamp doc_type."""
    for doc in ticket_docs:
        doc.metadata.setdefault("doc_type", "ticket")
    return ticket_docs


def build_all_chunks(sop_docs: list[Document], ticket_docs: list[Document]) -> list[Document]:
    chunks: list[Document] = []
    for sop in sop_docs:
        chunks.extend(chunk_sop(sop))
    chunks.extend(chunk_tickets(ticket_docs))
    return chunks
