"""Turn an error group + insight into safe, rendered remediation commands.

M8 default: deterministic mapping from error_type → relevant template ids, with
parameters extracted from the insight where possible. This needs no extra LLM
call (cheap, reliable) and is trivially testable. An LLM-driven selector can
plug in later behind the same function — but it would still be constrained to
returning template ids + params, never free-form commands.
"""

from app.ai.commands.catalog import CATALOG, InvalidCommandParams, render_command

# error_type (from InsightResult) → ordered template ids to suggest
_SUGGESTIONS: dict[str, list[str]] = {
    "Database Connectivity": [
        "k8s_get_pods",
        "k8s_logs",
        "linux_systemctl_status",
        "linux_pg_ready",
        "linux_port_check",
    ],
    "Resource Exhaustion": ["k8s_top_pods", "linux_mem", "linux_disk", "k8s_describe_pod"],
    "Performance Degradation": ["k8s_top_pods", "linux_mem", "k8s_logs"],
    "Application Error": ["k8s_logs", "k8s_describe_pod", "linux_journal"],
}
_DEFAULT = ["k8s_get_pods", "k8s_logs", "linux_disk"]

# Safe generic defaults for required params when we can't extract specifics.
_PARAM_DEFAULTS = {
    "namespace": "prod",
    "pod": "app-pod",
    "service": "postgresql",
    "host": "localhost",
    "port": "5432",
    "log_group": "/aws/app/logs",
}


def suggest_commands(error_type: str) -> list[dict[str, str]]:
    """Return [{command, description, domain}] for an error type — all validated."""
    template_ids = _SUGGESTIONS.get(error_type, _DEFAULT)
    out: list[dict[str, str]] = []
    for tid in template_ids:
        template = CATALOG[tid]
        params = {p.name: _PARAM_DEFAULTS[p.name] for p in template.params}
        try:
            rendered = render_command(tid, params)
        except InvalidCommandParams:
            continue  # defense in depth: skip anything that fails validation
        out.append(
            {"command": rendered, "description": template.description, "domain": template.domain}
        )
    return out
