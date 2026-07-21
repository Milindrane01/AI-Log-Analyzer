"""Parser + detector unit tests against realistic fixture lines."""

from app.parsing import detector
from app.parsing.parsers import REGISTRY
from app.parsing.parsers.jsonlines import JsonLinesParser
from app.parsing.parsers.logfmt import LogfmtParser
from app.parsing.parsers.plain import PlainParser
from app.parsing.parsers.syslog import SyslogParser

JSON_LINES = [
    '{"timestamp": "2026-07-15T10:12:14Z", "level": "error", "message": "DB timeout"}',
    '{"timestamp": "2026-07-15T10:12:15Z", "level": "info", "msg": "retrying"}',
]
SYSLOG_LINES = [
    "Jul 15 10:12:14 web-1 nginx[221]: upstream timed out while connecting",
    "Jul 15 10:12:15 web-1 systemd[1]: nginx.service: Failed with result 'timeout'",
]
LOGFMT_LINES = [
    'time=2026-07-15T10:12:14Z level=error msg="connection refused" service=api',
    'time=2026-07-15T10:12:15Z level=info msg="listening" port=8080',
]
PLAIN_LINES = [
    "2026-07-15 10:12:14 ERROR Database connection timeout",
    "Connection refused to PostgreSQL",
]


def test_json_parser_extracts_fields() -> None:
    entry = JsonLinesParser().parse_line(JSON_LINES[0])

    assert entry is not None
    assert entry.level == "error"
    assert entry.message == "DB timeout"
    assert entry.timestamp is not None and entry.timestamp.year == 2026


def test_syslog_parser_extracts_fields() -> None:
    entry = SyslogParser().parse_line(SYSLOG_LINES[1])

    assert entry is not None
    assert entry.level == "error"  # "Failed" keyword hint
    assert "nginx.service" in entry.message


def test_logfmt_parser_extracts_quoted_message() -> None:
    entry = LogfmtParser().parse_line(LOGFMT_LINES[0])

    assert entry is not None
    assert entry.level == "error"
    assert entry.message == "connection refused"


def test_plain_parser_handles_level_line_and_continuation() -> None:
    parser = PlainParser()
    first = parser.parse_line(PLAIN_LINES[0])
    cont = parser.parse_line(PLAIN_LINES[1])

    assert first is not None and first.level == "error"
    assert first.timestamp is not None
    assert cont is not None
    assert cont.level == "error"  # "refused" keyword heuristic
    assert cont.message == PLAIN_LINES[1]


def test_plain_parser_never_returns_none() -> None:
    parser = PlainParser()
    for weird in ["", "   ", "%%%###", "\t\t"]:
        assert parser.parse_line(weird) is not None


def test_detector_picks_each_format() -> None:
    assert detector.detect(JSON_LINES).name == "json"
    assert detector.detect(SYSLOG_LINES).name == "syslog"
    assert detector.detect(LOGFMT_LINES).name == "logfmt"
    assert detector.detect(PLAIN_LINES).name == "plain"


def test_detector_empty_input_falls_back_to_plain() -> None:
    assert detector.detect([]).name == "plain"


def test_registry_order_plain_is_last() -> None:
    assert REGISTRY[-1].name == "plain"  # fallback contract the detector relies on
