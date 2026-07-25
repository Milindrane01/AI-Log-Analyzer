"""Syslog (RFC 3164-style) parser: 'Jul 15 10:12:14 host proc[pid]: message'."""

import re
from datetime import datetime

from app.parsing.base import ParsedEntry, normalize_level

_SYSLOG = re.compile(
    r"^(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
    r"(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+(?P<proc>[\w./-]+)(?:\[(?P<pid>\d+)\])?:\s*"
    r"(?P<message>.*)$"
)
_MONTHS = {
    m: i
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1
    )
}
# Severity keywords inside the free-text message (syslog lines rarely carry a level field)
_LEVEL_HINT = re.compile(r"\b(error|err|warn|warning|crit|critical|fatal|fail(?:ed|ure)?)\b", re.I)


class SyslogParser:
    name = "syslog"

    def sniff(self, sample_lines: list[str]) -> float:
        if not sample_lines:
            return 0.0
        hits = sum(1 for line in sample_lines if _SYSLOG.match(line.strip()))
        return hits / len(sample_lines)

    def parse_line(self, line: str) -> ParsedEntry | None:
        match = _SYSLOG.match(line.strip())
        if match is None:
            return None
        # Syslog omits the year — assume current year (documented limitation).
        now = datetime.now()
        hh, mm, ss = (int(x) for x in match["time"].split(":"))
        timestamp = datetime(now.year, _MONTHS[match["month"]], int(match["day"]), hh, mm, ss)

        message = match["message"]
        hint = _LEVEL_HINT.search(message)
        level = normalize_level(hint.group(1)) if hint else "info"
        if hint and level is None:  # fail/failed/failure → error
            level = "error"
        return ParsedEntry(raw=line.rstrip("\n"), message=message, level=level, timestamp=timestamp)
