"""Format parser registry — ordered from most to least specific."""

from app.parsing.parsers.jsonlines import JsonLinesParser
from app.parsing.parsers.logfmt import LogfmtParser
from app.parsing.parsers.plain import PlainParser
from app.parsing.parsers.syslog import SyslogParser

# Order matters: detector prefers earlier parsers on score ties. Plain is the
# universal fallback and must stay last.
REGISTRY = [
    JsonLinesParser(),
    LogfmtParser(),
    SyslogParser(),
    PlainParser(),
]
