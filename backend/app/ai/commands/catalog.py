"""Curated remediation command catalog.

Every template is read-only/diagnostic. Parameters are regex-validated before
substitution — a namespace can only be `[a-z0-9-]`, never `; rm -rf /`.
"""

import re
from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class Param:
    name: str
    pattern: re.Pattern[str]
    example: str


@dataclass(slots=True, frozen=True)
class CommandTemplate:
    id: str
    domain: str  # linux | kubernetes | aws
    template: str  # e.g. "kubectl logs {pod} -n {namespace} --tail=100"
    description: str  # what it checks — shown to the user
    mutating: bool = False  # M8 ships only read-only; field reserved for future
    params: tuple[Param, ...] = field(default_factory=tuple)


# Reusable parameter validators — deliberately strict.
_NAMESPACE = Param("namespace", re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$"), "prod")
_POD = Param("pod", re.compile(r"^[a-z0-9][a-z0-9.-]{0,252}$"), "api-7d9f8")
_SERVICE = Param("service", re.compile(r"^[a-zA-Z0-9@._-]{1,128}$"), "postgresql")
_HOST = Param("host", re.compile(r"^[a-zA-Z0-9.-]{1,253}$"), "db.internal")
_PORT = Param("port", re.compile(r"^[0-9]{1,5}$"), "5432")
_LOG_GROUP = Param("log_group", re.compile(r"^[a-zA-Z0-9/_.-]{1,512}$"), "/aws/rds/instance")

CATALOG: dict[str, CommandTemplate] = {
    t.id: t
    for t in [
        # --- kubernetes ---
        CommandTemplate(
            "k8s_get_pods",
            "kubernetes",
            "kubectl get pods -n {namespace}",
            "List pods and their status in a namespace",
            params=(_NAMESPACE,),
        ),
        CommandTemplate(
            "k8s_describe_pod",
            "kubernetes",
            "kubectl describe pod {pod} -n {namespace}",
            "Show pod events, restarts, and scheduling issues",
            params=(_POD, _NAMESPACE),
        ),
        CommandTemplate(
            "k8s_logs",
            "kubernetes",
            "kubectl logs {pod} -n {namespace} --tail=200",
            "Read recent logs from a pod",
            params=(_POD, _NAMESPACE),
        ),
        CommandTemplate(
            "k8s_top_pods",
            "kubernetes",
            "kubectl top pods -n {namespace}",
            "Show CPU/memory usage per pod",
            params=(_NAMESPACE,),
        ),
        # --- linux ---
        CommandTemplate(
            "linux_systemctl_status",
            "linux",
            "systemctl status {service}",
            "Check whether a service is running",
            params=(_SERVICE,),
        ),
        CommandTemplate(
            "linux_journal",
            "linux",
            "journalctl -u {service} --since '1 hour ago'",
            "Read recent service logs",
            params=(_SERVICE,),
        ),
        CommandTemplate(
            "linux_port_check",
            "linux",
            "nc -zv {host} {port}",
            "Test TCP reachability to a host:port",
            params=(_HOST, _PORT),
        ),
        CommandTemplate(
            "linux_pg_ready",
            "linux",
            "pg_isready -h {host} -p {port}",
            "Check PostgreSQL accepts connections",
            params=(_HOST, _PORT),
        ),
        CommandTemplate(
            "linux_disk", "linux", "df -h", "Show disk usage (full disks cause many failures)"
        ),
        CommandTemplate("linux_mem", "linux", "free -m", "Show memory usage (OOM diagnosis)"),
        # --- aws ---
        CommandTemplate(
            "aws_logs_tail",
            "aws",
            "aws logs tail {log_group} --since 1h",
            "Tail a CloudWatch log group",
            params=(_LOG_GROUP,),
        ),
        CommandTemplate(
            "aws_rds_describe",
            "aws",
            "aws rds describe-db-instances",
            "List RDS instances and their status",
        ),
    ]
}


class InvalidCommandParams(ValueError):
    """Raised when a suggested template id is unknown or params fail validation."""


def render_command(template_id: str, params: dict[str, str]) -> str:
    """Render a catalog template with validated params, or raise."""
    template = CATALOG.get(template_id)
    if template is None:
        raise InvalidCommandParams(f"Unknown command template: {template_id}")
    values: dict[str, str] = {}
    for param in template.params:
        value = params.get(param.name, "")
        if not param.pattern.match(value):
            raise InvalidCommandParams(f"Invalid {param.name!r} for {template_id}")
        values[param.name] = value
    return template.template.format(**values)
