"""Format detection: sample the head of the file, score every parser, pick the best."""

import structlog

from app.parsing.base import LogParser
from app.parsing.parsers import REGISTRY

log = structlog.get_logger()

SAMPLE_SIZE = 50  # lines — enough signal, negligible cost
MIN_SCORE = 0.5  # below this, no specific format is trusted → plain fallback


def detect(sample_lines: list[str]) -> LogParser:
    """Pick the parser with the best sniff score on non-empty sample lines."""
    sample = [line for line in sample_lines if line.strip()][:SAMPLE_SIZE]
    best: LogParser = REGISTRY[-1]  # plain fallback
    best_score = 0.0
    for parser in REGISTRY[:-1]:  # score specific parsers only
        score = parser.sniff(sample)
        if score > best_score:
            best, best_score = parser, score
    chosen = best if best_score >= MIN_SCORE else REGISTRY[-1]
    log.info("log_format_detected", format=chosen.name, score=round(best_score, 2))
    return chosen
