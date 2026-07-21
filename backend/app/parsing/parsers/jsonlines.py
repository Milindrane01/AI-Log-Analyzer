"""JSON-lines parser: one JSON object per line (structlog, bunyan, evlog NDJSON…)."""

import json
from typing import Any

from app.parsing.base import ParsedEntry, normalize_level, parse_timestamp

_TS_KEYS = ("timestamp", "time", "ts", "@timestamp", "datetime")
_LEVEL_KEYS = ("level", "severity", "lvl", "loglevel", "log.level")
_MSG_KEYS = ("message", "msg", "event", "log")


def _first(obj: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in obj:
            return obj[key]
    return None


class JsonLinesParser:
    name = "json"

    def sniff(self, sample_lines: list[str]) -> float:
        if not sample_lines:
            return 0.0
        hits = sum(1 for line in sample_lines if self.parse_line(line) is not None)
        return hits / len(sample_lines)

    def parse_line(self, line: str) -> ParsedEntry | None:
        line = line.strip()
        if not line.startswith("{"):
            return None
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            return None
        if not isinstance(obj, dict):
            return None

        raw_ts = _first(obj, _TS_KEYS)
        message = _first(obj, _MSG_KEYS)
        return ParsedEntry(
            raw=line,
            message=str(message) if message is not None else line,
            level=normalize_level(str(_first(obj, _LEVEL_KEYS) or "") or None),
            timestamp=parse_timestamp(str(raw_ts)) if raw_ts else None,
        )
