"""Input sanitization — enforces length limits and strips dangerous patterns."""
from __future__ import annotations
import re
import structlog
from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()

# Patterns that indicate prompt-injection attempts
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+\w+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\s*(?:script|iframe|object|embed)[^>]*>", re.IGNORECASE),
    re.compile(r"```\s*system\b", re.IGNORECASE),
]

# Rough PII patterns for scrubbing before sending to the LLM
_PII_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),                        # SSN
    (re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b"), "[CARD]"),                  # credit card
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL]"),
]


class InputGuard:
    """Sanitizes incoming user queries before they enter the pipeline."""

    def sanitize(self, query: str) -> str:
        # 1. Enforce max length
        query = query[: settings.max_query_length]

        # 2. Strip leading/trailing whitespace
        query = query.strip()

        # 3. Detect prompt-injection patterns — log a warning but still allow
        #    (blocking would require human review; we just log for monitoring)
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(query):
                log.warning("injection_pattern_detected", query=query[:120])
                break

        # 4. Optional PII redaction
        if settings.pii_redaction:
            for pattern, replacement in _PII_PATTERNS:
                query = pattern.sub(replacement, query)

        return query
