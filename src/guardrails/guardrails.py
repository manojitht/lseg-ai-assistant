from __future__ import annotations
import re
from dataclasses import dataclass, field
from src import config
from src.ingestion.document_loader import Document



_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "Access":   ["vpn", "mfa", "account", "lockout", "locked", "password", "token", "reset", "access"],
    "Deploy":   ["deploy", "deployment", "rollback", "production", "release", "pipeline"],
    "Database": ["schema", "mismatch", "query", "database", "latency", "migration", "data", "db"],
}


_ANOMALY_PATTERNS = [
    re.compile(r"remote.{0,20}mfa.{0,20}reset", re.IGNORECASE),
    re.compile(r"mfa.{0,20}reset.{0,20}(phone|email|call|urgent|remote)", re.IGNORECASE),
    re.compile(r"(executive|ciso|manager).{0,30}(approval|approved|authoris)", re.IGNORECASE),
    re.compile(r"(urgent|emergency).{0,30}(mfa|reset|access)", re.IGNORECASE),
    re.compile(r"bypass.{0,20}(mfa|authentication|policy)", re.IGNORECASE),
]

_LEGITIMATE_EXCEPTION_ID = "TKT-7421"  # documented in SOP-001 § Exception Handling


@dataclass
class GuardrailResult:
    flagged: bool = False
    low_confidence: bool = False
    domain_mismatch: bool = False
    anomaly_note: str = ""
    domain_note: str = ""
    detected_query_domain: str = ""
    top_score: float = 0.0



def check_confidence(scores: list[float]) -> bool:
    """Return True if confidence is too low to proceed with LLM call."""
    return not scores or max(scores) < config.CONFIDENCE_THRESHOLD


def check(query: str, docs: list[Document], scores: list[float]) -> GuardrailResult:
    result = GuardrailResult(top_score=max(scores) if scores else 0.0)

    # Guardrail 1: Confidence
    if check_confidence(scores):
        result.low_confidence = True
        result.flagged = True
        return result

    # Guardrail 2: Domain validation
    query_domain = _detect_domain(query)
    result.detected_query_domain = query_domain
    if query_domain and docs:
        top_doc_domain = docs[0].metadata.get("category") or _detect_domain(docs[0].text)
        if top_doc_domain and top_doc_domain != query_domain:
            result.domain_mismatch = True
            result.domain_note = (
                f"Note: query appears to be about '{query_domain}' but the "
                f"top retrieved document relates to '{top_doc_domain}'. "
                "Answer may be approximate."
            )

    # Guardrail 3: Policy anomaly (MFA / access social engineering)
    anomaly = _detect_anomaly(query, docs)
    if anomaly:
        result.flagged = True
        result.anomaly_note = anomaly

    return result



def _detect_domain(text: str) -> str:
    text_lower = text.lower()
    best_domain, best_count = "", 0
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count, best_domain = count, domain
    return best_domain


def _detect_anomaly(query: str, docs: list[Document]) -> str:
    combined = query + " " + " ".join(d.text for d in docs if d.metadata.get("doc_type") == "ticket")

    pattern_hit = any(p.search(combined) for p in _ANOMALY_PATTERNS)
    if not pattern_hit:
        return ""

    # Check if this is the one legitimate exception
    if _LEGITIMATE_EXCEPTION_ID in combined:
        return (
            f"POLICY NOTE: A remote MFA reset reference was detected. "
            f"The only documented exception is {_LEGITIMATE_EXCEPTION_ID} "
            "(CISO-approved with biometric verification, per SOP-001 § Exception Handling). "
            "All other remote reset requests are prohibited."
        )

    return (
        "POLICY ANOMALY DETECTED: This request matches a pattern associated with "
        "social-engineering attempts (remote MFA reset via phone/urgency/claimed approvals). "
        "Per SOP-001 and MFA Reset Policy, remote MFA resets are NOT permitted under any "
        "circumstances. The user must visit a regional hub in person. "
        "Do NOT process this request remotely. Escalate to Security-Ops for review."
    )
