"""Freeform parser — the universal fallback. Never returns None.

Handles the common '2026-07-15 10:12:14 ERROR message' shape, plus continuation
lines (stack traces) with no timestamp/level at all.
"""

import re

from app.parsing.base import ParsedEntry, normalize_level, parse_timestamp

_LINE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?"
    r"\s*\[?(?P<level>DEBUG|INFO|NOTICE|WARN(?:ING)?|ERROR|ERR|CRIT(?:ICAL)?|FATAL|TRACE)?\]?"
    r"[:\s-]*(?P<message>.*)$",
    re.IGNORECASE,
)
_LEVEL_HINT = re.compile(r"\b(error|exception|fail(?:ed|ure)?|timeout|refused|denied)\b", re.I)


class PlainParser:
    name = "plain"

    def sniff(self, sample_lines: list[str]) -> float:
        return 0.05  # tiny non-zero score: always a candidate, never preferred

    def parse_line(self, line: str) -> ParsedEntry | None:
        stripped = line.rstrip("\n")
        match = _LINE.match(stripped.strip())
        if match is None or not stripped.strip():
            return ParsedEntry(raw=stripped, message=stripped)

        level = normalize_level(match["level"])
        message = match["message"] or stripped
        if level is None and _LEVEL_HINT.search(message):
            level = "error"  # keyword heuristic for level-less lines
        return ParsedEntry(
            raw=stripped,
            message=message,
            level=level,
            timestamp=parse_timestamp(match["ts"]) if match["ts"] else None,
        )
