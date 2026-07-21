"""Error fingerprinting: same problem → same hash, regardless of variable noise.

The idea (how Sentry groups errors): strip everything request-specific from the
message — ids, timestamps, IPs, numbers, quoted values, paths — leaving a stable
TEMPLATE. Hash(level + template) = the group fingerprint.

    "Connection timeout for user 8231 from 10.0.3.7"
    "Connection timeout for user 9440 from 10.9.1.2"
        → both: "connection timeout for user <n> from <ip>"  → one group, count=2
"""

import hashlib
import re

_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "<uuid>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"), "<ts>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b"), "<ip>"),
    (re.compile(r"\b[0-9a-f]{12,64}\b", re.I), "<hex>"),
    (re.compile(r"'[^']*'"), "<str>"),
    (re.compile(r'"[^"]*"'), "<str>"),
    (re.compile(r"(?:/[\w.\-]+){2,}"), "<path>"),
    (re.compile(r"\b\d+(?:\.\d+)?\b"), "<n>"),  # LAST: after ips/timestamps consumed digits
    (re.compile(r"\s+"), " "),
]


def template_of(message: str) -> str:
    """Normalize a message into its stable template."""
    result = message.strip().lower()
    for pattern, replacement in _RULES:
        result = pattern.sub(replacement, result)
    return result.strip()[:500]  # cap: templates are keys, not documents


def fingerprint(level: str, message: str) -> tuple[str, str]:
    """Return (sha256 fingerprint, template) for a log message."""
    template = template_of(message)
    digest = hashlib.sha256(f"{level}|{template}".encode()).hexdigest()
    return digest, template
