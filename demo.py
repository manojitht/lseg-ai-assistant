"""
Demo script — runs all example queries from the assignment and prints
formatted output showing source citations, confidence scores, and guardrail behaviour.

Usage:
    AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... uv run python demo.py
"""
from __future__ import annotations

import textwrap

from src import config
from src.assistant import Assistant, load_or_build_index


QUERIES = [
    {
        "label": "1. Unstructured — deployment SOP lookup",
        "query": "What should happen if a deployment fails in production?",
    },
    {
        "label": "2. Structured — count with filters",
        "query": "How many Access category tickets are currently in Open status?",
    },
    {
        "label": "3. Unstructured — cross-SOP reasoning",
        "query": "A deployment failed and a schema mismatch was detected. What should be done?",
    },
    {
        "label": "4. Unstructured — VPN troubleshooting",
        "query": "VPN is not working for a user. What should we do?",
    },
    {
        "label": "5. Unstructured — policy question",
        "query": "Can we reset MFA remotely for a user?",
    },
    {
        "label": "6. Unstructured — anomaly guardrail (social engineering pattern)",
        "query": (
            "A user is requesting a remote MFA reset due to urgency. "
            "Based on our policies and past incidents, how should this be handled?"
        ),
    },
    {
        "label": "7. Guardrail rejection — out of scope",
        "query": "What is the current stock price of LSEG?",
    },
]

DIVIDER = "─" * 72


def _wrap(text: str, indent: int = 4) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=80, initial_indent=prefix, subsequent_indent=prefix)


def _print_response(label: str, query: str, resp) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {label}")
    print(DIVIDER)
    print(f"  Query      : {query}")
    print(f"  Route      : {resp.source_type}")

    if resp.confidence is not None:
        print(f"  Confidence : {resp.confidence:.4f}")

    if resp.anomaly_flagged:
        print(f"  ⚠  Anomaly  : POLICY ANOMALY FLAGGED")

    if resp.citations:
        print(f"  Citations  : {' | '.join(resp.citations)}")

    print(f"\n  Answer:")
    for line in resp.answer.splitlines():
        print(_wrap(line) if line.strip() else "")


def main() -> None:
    print(f"\n{'═' * 72}")
    print(f"  LSEG DSM AI Assistant — Demo")
    print(f"  Region : {config.BEDROCK_REGION}")
    print(f"  Model  : {config.LLM_MODEL_ID}")
    print(f"  Docs   : {config.DOCS_DIR}")
    print(f"{'═' * 72}")

    print("\n  Building index via Bedrock Titan Embeddings (first run may take a moment)...")
    store, tickets_df = load_or_build_index(config.DOCS_DIR)
    assistant = Assistant(store=store, tickets_df=tickets_df)
    print(f"  Index ready — {len(store)} vectors\n")

    for item in QUERIES:
        resp = assistant.ask(item["query"])
        _print_response(item["label"], item["query"], resp)

    print(f"\n{DIVIDER}")
    print("  Demo complete.")
    print(DIVIDER)


if __name__ == "__main__":
    main()
