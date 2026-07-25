"""Deterministic mock provider: keyword heuristics, zero network, zero cost.

Serves two jobs: (1) the entire test suite runs offline; (2) the app demos
end-to-end without an API key (AI features visibly work, marked as mock model).
"""

from collections.abc import AsyncIterator
from typing import Any

from app.ai.providers.base import (
    InsightRequest,
    InsightResult,
    ProviderResponse,
    ProviderUsage,
)

_RULES: list[tuple[tuple[str, ...], dict[str, Any]]] = [
    (
        ("database", "postgres", "connection", "timeout", "refused"),
        {
            "severity": "critical",  # content knows better than the log level
            "error_type": "Database Connectivity",
            "root_cause": "The application cannot establish a connection to the database.",
            "possible_reasons": [
                "Database service is down",
                "Wrong credentials or connection string",
                "Firewall or network issue",
                "Connection pool exhausted",
            ],
            "suggested_fix": "Verify database status and connectivity from the application host.",
            "recommended_commands": [
                "kubectl get pods",
                "kubectl describe pod postgres-0",
                "kubectl logs postgres-0 --tail=100",
                "systemctl status postgresql",
            ],
            "confidence": 0.94,
        },
    ),
    (
        ("memory", "oom", "killed"),
        {
            "error_type": "Resource Exhaustion",
            "root_cause": "A process ran out of memory and was terminated.",
            "possible_reasons": ["Memory leak", "Undersized container limits", "Traffic spike"],
            "suggested_fix": "Inspect memory usage trends and raise limits or fix the leak.",
            "recommended_commands": ["kubectl top pods", "free -m", "dmesg | tail"],
            "confidence": 0.88,
        },
    ),
    (
        ("slow", "query", "latency"),
        {
            "error_type": "Performance Degradation",
            "root_cause": "Operations are exceeding expected duration thresholds.",
            "possible_reasons": ["Missing index", "Lock contention", "Resource saturation"],
            "suggested_fix": "Identify the slow operation and profile it.",
            "recommended_commands": ["kubectl top pods"],
            "confidence": 0.75,
        },
    ),
]

_FALLBACK = {
    "error_type": "Application Error",
    "root_cause": "An application-level error occurred; see sample log lines.",
    "possible_reasons": ["Bug in application code", "Unexpected input", "Dependency failure"],
    "suggested_fix": "Inspect the sample lines and the surrounding log context.",
    "recommended_commands": [],
    "confidence": 0.5,
}

_SEVERITY_BY_LEVEL = {"critical": "critical", "error": "high", "warning": "medium"}


class MockLLMProvider:
    def __init__(self) -> None:
        self.calls = 0  # tests assert on this (cache verification)

    async def analyze_group(self, request: InsightRequest) -> ProviderResponse:
        self.calls += 1
        haystack = f"{request.template} {' '.join(request.sample_lines)}".lower()
        chosen = _FALLBACK
        best = 1  # require at least 2 keyword hits to beat fallback
        for keywords, rule in _RULES:
            hits = sum(1 for kw in keywords if kw in haystack)
            if hits > best:
                best, chosen = hits, rule
        rule = dict(chosen)
        severity = rule.pop("severity", None) or _SEVERITY_BY_LEVEL.get(request.level, "low")
        result = InsightResult(
            severity=severity,
            explanation=(
                f"This group occurred {request.count} time(s). {rule['root_cause']} "
                "In simple terms: the system tried to do something and the other side "
                "did not respond as expected."
            ),
            **rule,
        )
        return ProviderResponse(result=result, usage=ProviderUsage(model="mock"))

    async def stream_chat(self, system: str, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """Grounded canned answer: cite the first line range found in the context."""
        self.calls += 1
        context = messages[-1]["content"] if messages else ""
        import re as _re

        match = _re.search(r"\[lines (\d+)-(\d+)\]\n(.*)", context)
        if match:
            first_line = match.group(3).splitlines()[0][:120]
            answer = (
                f"Based on [lines {match.group(1)}-{match.group(2)}], the log shows: "
                f'"{first_line}". This is the relevant evidence for your question.'
            )
        else:
            answer = "I don't see that in this log."
        for word in answer.split(" "):
            yield word + " "
