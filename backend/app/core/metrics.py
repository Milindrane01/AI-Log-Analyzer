"""Prometheus metrics — dependency-free text exposition.

We hand-roll the /metrics text format instead of pulling prometheus_client:
the format is trivial, and one fewer dependency matters (same philosophy as
using httpx over vendor SDKs). RED method: Rate, Errors, Duration per route.
"""

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from threading import Lock

from fastapi import FastAPI, Request, Response

_lock = Lock()
_request_count: dict[tuple[str, str, int], int] = defaultdict(int)  # (method, path, status) → n
_duration_sum: dict[tuple[str, str], float] = defaultdict(float)  # (method, path) → seconds
_duration_count: dict[tuple[str, str], int] = defaultdict(int)


def _route_template(request: Request) -> str:
    """Group by route TEMPLATE (/analyses/{id}), never raw path — else every
    UUID becomes its own metric series and Prometheus melts (high cardinality)."""
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


def setup_metrics(app: FastAPI) -> None:
    @app.middleware("http")
    async def _track(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        path = _route_template(request)
        if path != "/metrics":  # don't measure the scrape itself
            with _lock:
                _request_count[(request.method, path, response.status_code)] += 1
                _duration_sum[(request.method, path)] += elapsed
                _duration_count[(request.method, path)] += 1
        return response

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(content=_render(), media_type="text/plain; version=0.0.4")


def _render() -> str:
    lines = [
        "# HELP http_requests_total Total HTTP requests.",
        "# TYPE http_requests_total counter",
    ]
    with _lock:
        for (method, path, status), n in sorted(_request_count.items()):
            lines.append(
                f'http_requests_total{{method="{method}",path="{path}",status="{status}"}} {n}'
            )
        lines += [
            "# HELP http_request_duration_seconds_sum Sum of request durations.",
            "# TYPE http_request_duration_seconds_sum counter",
        ]
        for (method, path), total in sorted(_duration_sum.items()):
            lines.append(
                f'http_request_duration_seconds_sum{{method="{method}",path="{path}"}} {total:.6f}'
            )
        lines += [
            "# HELP http_request_duration_seconds_count Count of measured requests.",
            "# TYPE http_request_duration_seconds_count counter",
        ]
        for (method, path), n in sorted(_duration_count.items()):
            lines.append(
                f'http_request_duration_seconds_count{{method="{method}",path="{path}"}} {n}'
            )
    return "\n".join(lines) + "\n"


def reset() -> None:
    """Test hook."""
    with _lock:
        _request_count.clear()
        _duration_sum.clear()
        _duration_count.clear()
