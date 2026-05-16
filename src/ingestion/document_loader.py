from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd


@dataclass
class Document:
    text: str
    metadata: dict = field(default_factory=dict)


def load_sop_documents(docs_dir: str) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(Path(docs_dir).glob("SOP-*.md")):
        text = path.read_text(encoding="utf-8")
        sop_id = path.stem.split("-")[0] + "-" + path.stem.split("-")[1]  # e.g. SOP-001
        documents.append(Document(text=text, metadata={"source": sop_id, "filename": path.name}))
    return documents


def load_tickets_dataframe(docs_dir: str) -> pd.DataFrame:
    csv_path = Path(docs_dir) / "INCIDENT-TICKETS.csv"
    df = pd.read_csv(csv_path, parse_dates=["Created_Date"])
    df.columns = [c.strip() for c in df.columns]
    df["ID"]       = df["ID"].str.strip()
    df["Category"] = df["Category"].str.strip()
    df["Status"]   = df["Status"].str.strip()
    df["Priority"] = df["Priority"].str.strip()
    return df


def load_ticket_documents(df: pd.DataFrame) -> list[Document]:
    documents: list[Document] = []
    for _, row in df.iterrows():
        text = (
            f"{row['ID']} | Category: {row['Category']} | "
            f"Priority: {row['Priority']} | Status: {row['Status']} | "
            f"Description: {row['Description']}"
        )
        documents.append(Document(
            text=text,
            metadata={
                "source":   row["ID"],
                "category": row["Category"],
                "priority": row["Priority"],
                "status":   row["Status"],
                "doc_type": "ticket",
            },
        ))
    return documents
