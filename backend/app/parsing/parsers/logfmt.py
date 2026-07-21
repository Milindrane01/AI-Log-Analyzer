"""logfmt parser: key=value pairs (heroku, Go kit, many infra tools)."""

import re

from app.parsing.base import ParsedEntry, normalize_level, parse_timestamp

# key=value where value is bare or double-quoted (with escapes)
_PAIR = re.compile(r'([A-Za-z0-9_.@-]+)=("(?:[^"\\]|\\.)*"|\S+)')


class LogfmtParser:
    name = "logfmt"

    def sniff(self, sample_lines: list[str]) -> float:
        if not sample_lines:
            return 0.0
        hits = sum(1 for line in sample_lines if self.parse_line(line) is not None)
        return hits / len(sample_lines)

    def parse_line(self, line: str) -> ParsedEntry | None:
        line = line.strip()
        pairs = dict(_PAIR.findall(line))
        # Require at least 2 pairs AND a known logfmt-ish key — one accidental
        # foo=bar inside prose must not classify a plain log as logfmt.
        if len(pairs) < 2 or not ({"level", "msg", "time", "ts"} & pairs.keys()):
            return None

        def unquote(value: str | None) -> str | None:
            if value and value.startswith('"') and value.endswith('"'):
                return value[1:-1].replace('\\"', '"')
            return value

        raw_ts = unquote(pairs.get("time") or pairs.get("ts"))
        message = unquote(pairs.get("msg") or pairs.get("message"))
        return ParsedEntry(
            raw=line,
            message=message if message else line,
            level=normalize_level(unquote(pairs.get("level"))),
            timestamp=parse_timestamp(raw_ts) if raw_ts else None,
        )
