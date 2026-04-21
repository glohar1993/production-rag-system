"""Output guard — scrubs PII and sensitive patterns from generated answers."""
from __future__ import annotations
import re
import structlog
from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()

_REDACTIONS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN REDACTED]"),
    (re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b"), "[CARD REDACTED]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL REDACTED]"),
    (re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"), "[PHONE REDACTED]"),
]


class OutputGuard:
    """Applies PII redaction to LLM-generated output."""

    def redact(self, text: str) -> str:
        if not settings.pii_redaction:
            return text
        for pattern, replacement in _REDACTIONS:
            text = pattern.sub(replacement, text)
        return text
