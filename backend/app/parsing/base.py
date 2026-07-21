"""Parser contract + shared types.

Parsers form a REGISTRY (open-closed principle): adding a format = one new
class + one registry entry. No if/else ladder to grow unboundedly.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

# Normalized level vocabulary. Everything maps into this.
LEVELS = {"debug", "info", "warning", "error", "critical"}

_LEVEL_ALIASES = {
    "warn": "warning",
    "err": "error",
    "fatal": "critical",
    "crit": "critical",
    "emerg": "critical",
    "panic": "critical",
    "trace": "debug",
    "notice": "info",
}


def normalize_level(raw: str | None) -> str | None:
    if raw is None:
        return None
    level = raw.strip().lower()
    level = _LEVEL_ALIASES.get(level, level)
    return level if level in LEVELS else None


@dataclass(slots=True)
class ParsedEntry:
    """One log line, normalized."""

    raw: str
    message: str
    level: str | None = None  # normalized, or None if undetectable
    timestamp: datetime | None = None


class LogParser(Protocol):
    """Contract every format parser implements."""

    name: str

    def sniff(self, sample_lines: list[str]) -> float:
        """Return 0.0–1.0: fraction of sample lines this parser understands."""
        ...

    def parse_line(self, line: str) -> ParsedEntry | None:
        """Parse one line; None means 'not my format' (detector fallback logic)."""
        ...


# Common timestamp formats tried in order. Cheap and covers the usual suspects.
_TS_FORMATS = (
    "%Y-%m-%d %H:%M:%S,%f",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
)


def parse_timestamp(raw: str) -> datetime | None:
    raw = raw.strip().replace("Z", "+00:00") if raw.endswith("Z") else raw.strip()
    for fmt in _TS_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None
