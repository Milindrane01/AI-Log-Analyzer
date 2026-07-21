"""Structured logging setup (structlog).

We are a log-analysis product — our own logs must be machine-parseable.
In production every log line is a single JSON object (ingestable by
Loki/ELK/CloudWatch); in development it's pretty, colored console output.

Usage anywhere in the app:

    import structlog
    log = structlog.get_logger()
    log.info("log_file_uploaded", file_id=str(fid), size_bytes=n)

Convention: event name is a snake_case NOUN PHRASE, context goes in
key-value pairs — never f-strings. That's what makes logs queryable.
"""

import logging
import sys

import structlog


def configure_logging(log_level: str = "INFO", json_logs: bool = True) -> None:
    """Configure stdlib logging + structlog once, at application startup."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Shared processors: enrich every event with level, timestamp, logger name.
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,  # request-scoped context (request_id later)
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,  # exc_info=True → structured traceback
    ]

    renderer: structlog.types.Processor
    if json_logs:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (uvicorn, sqlalchemy, celery) to stdout at the same
    # level so third-party logs aren't silently dropped or double-formatted.
    logging.basicConfig(level=level, stream=sys.stdout, format="%(message)s")
