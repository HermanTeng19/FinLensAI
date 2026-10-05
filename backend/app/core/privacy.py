"""FinLens AI Privacy, Security & Data Protection Framework.

Provides:
1. Regex-based sensitive data redaction for credit cards (PAN), SIN/SSNs, and bank account numbers.
2. Logging filter (SensitiveDataFilter) that redacts log outputs automatically.
3. Security & Anti-Caching middleware (PrivacyHeadersMiddleware) that prevents persistence of
   sensitive financial intelligence on client/proxy caches and enforces modern browser security headers.
"""

import logging
import re

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# ---------------------------------------------------------------------------
# Sensitive Data Regex Patterns
# ---------------------------------------------------------------------------

# PAN / Credit Card: 13 to 19 digits, optional spaces or dashes
# Matches common Visa, Mastercard, Amex, Discover formats
RE_CREDIT_CARD = re.compile(
    r"\b(?:\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{1,7}|\d{4}[ -]?\d{6}[ -]?\d{5})\b"
)

# Canadian SIN (3-3-3 or 9 digits) and US SSN (3-2-4)
RE_SSN_SIN = re.compile(r"\b(?:\d{3}[ -]\d{2}[ -]\d{4}|\d{3}[ -]\d{3}[ -]\d{3})\b")

# Bank Account Numbers & Transit numbers when preceded by common keywords
RE_BANK_ACCOUNT = re.compile(
    r"(?i)\b((?:acct|account|transit|institution|inst|routing)[#:\s]+)(\d{4,17})\b"
)


def redact_sensitive_text(text: str) -> str:
    """Mask credit card PANs, SIN/SSNs, and bank account numbers in any text."""
    if not isinstance(text, str):
        return text

    # Redact bank account / transit numbers (keep keyword, mask digits)
    text = RE_BANK_ACCOUNT.sub(r"\g<1>[REDACTED_ACCOUNT]", text)
    # Redact SIN / SSN
    text = RE_SSN_SIN.sub("[REDACTED_ID]", text)
    # Redact Credit Cards / PANs
    text = RE_CREDIT_CARD.sub("[REDACTED_CARD]", text)

    return text


class SensitiveDataFilter(logging.Filter):
    """Logging filter that redacts sensitive financial information in log records and attaches correlation_id."""

    def filter(self, record: logging.LogRecord) -> bool:
        from app.core.telemetry import correlation_id_ctx

        record.correlation_id = correlation_id_ctx.get() or "-"
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: (redact_sensitive_text(v) if isinstance(v, str) else v)
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_sensitive_text(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True


def setup_privacy_logging():
    """Attach the SensitiveDataFilter to root and uvicorn loggers."""
    privacy_filter = SensitiveDataFilter()
    root_logger = logging.getLogger()
    root_logger.addFilter(privacy_filter)

    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        lgr = logging.getLogger(logger_name)
        lgr.addFilter(privacy_filter)


class PrivacyHeadersMiddleware(BaseHTTPMiddleware):
    """Injects zero-retention caching rules and strict security headers into every response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Zero-retention caching: financial records, analysis, and insights MUST NOT be cached
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0, private"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # Modern Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=(), payment=()"
        )

        return response
