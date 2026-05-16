"""
Deterministic structured query handler for INCIDENT-TICKETS data.

Structured queries (counting, filtering) are handled via pandas — never via LLM.
This guarantees exact, auditable answers for questions like:
  "How many Access tickets are currently Open?"
  "List all P1 Deploy tickets that are Escalated"

Unrecognised phrasing returns None → caller falls back to the RAG pipeline.
"""
from __future__ import annotations

import re

import pandas as pd



_COUNT_PATTERNS = re.compile(
    r"\b(how many|count|number of|total|tally)\b", re.IGNORECASE
)
_LIST_PATTERNS = re.compile(
    r"\b(list|show|give me|display|which tickets|what tickets)\b", re.IGNORECASE
)
_STATUS_MAP = {
    "open":        "Open",
    "in progress": "In-Progress",
    "in-progress": "In-Progress",
    "escalated":   "Escalated",
}
_PRIORITY_MAP = {"p1": "P1", "p2": "P2", "p3": "P3"}
_CATEGORY_MAP = {
    "access":   "Access",
    "database": "Database",
    "deploy":   "Deploy",
    "db":       "Database",
}


def is_structured_query(query: str) -> bool:
    return bool(_COUNT_PATTERNS.search(query) or _LIST_PATTERNS.search(query))


def handle(query: str, df: pd.DataFrame) -> str:
    """
    Parse the query for filters, apply them to the DataFrame deterministically,
    and return a human-readable answer string.
    """
    q_lower = query.lower()

    # Extract filters
    status   = _extract(q_lower, _STATUS_MAP)
    priority = _extract(q_lower, _PRIORITY_MAP)
    category = _extract(q_lower, _CATEGORY_MAP)

    filtered = _apply_filters(df, status, priority, category)

    # Determine response type
    if _COUNT_PATTERNS.search(query):
        return _count_response(filtered, status, priority, category)
    else:
        return _list_response(filtered, status, priority, category)



def _extract(text: str, mapping: dict[str, str]) -> str | None:
    for key, val in mapping.items():
        if key in text:
            return val
    return None


def _apply_filters(
    df: pd.DataFrame,
    status: str | None,
    priority: str | None,
    category: str | None,
) -> pd.DataFrame:
    mask = pd.Series([True] * len(df), index=df.index)
    if status:
        mask &= df["Status"] == status
    if priority:
        mask &= df["Priority"] == priority
    if category:
        mask &= df["Category"] == category
    return df[mask]


def _filter_description(status: str | None, priority: str | None, category: str | None) -> str:
    parts = []
    if category:
        parts.append(f"Category={category}")
    if status:
        parts.append(f"Status={status}")
    if priority:
        parts.append(f"Priority={priority}")
    return ", ".join(parts) if parts else "all tickets"


def _count_response(
    filtered: pd.DataFrame,
    status: str | None,
    priority: str | None,
    category: str | None,
) -> str:
    desc  = _filter_description(status, priority, category)
    count = len(filtered)
    return (
        f"There are **{count}** ticket(s) matching [{desc}].\n\n"
        f"_Source: structured ticket data (deterministic query — not LLM-generated)_"
    )


def _list_response(
    filtered: pd.DataFrame,
    status: str | None,
    priority: str | None,
    category: str | None,
) -> str:
    desc = _filter_description(status, priority, category)
    if filtered.empty:
        return (
            f"No tickets found matching [{desc}].\n\n"
            "_Source: structured ticket data (deterministic query)_"
        )
    rows = filtered[["ID", "Priority", "Status", "Category", "Description"]].head(20)
    lines = [f"Tickets matching [{desc}]:\n"]
    for _, row in rows.iterrows():
        lines.append(
            f"- **{row['ID']}** | {row['Priority']} | {row['Status']} | "
            f"{row['Category']} — {row['Description'][:80]}..."
        )
    lines.append(
        f"\n_Showing {len(rows)} of {len(filtered)} result(s). "
        "Source: structured ticket data (deterministic query)_"
    )
    return "\n".join(lines)
