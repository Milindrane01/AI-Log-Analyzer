"""Incident report generation: assemble a postmortem-ready markdown document.

Deterministic assembly from already-computed analysis data (groups + insights +
commands) — no extra LLM call needed. The AI value was spent in M4; the report
composes it. This keeps report generation fast, free, and reproducible.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.commands.selector import suggest_commands
from app.models import Analysis, ErrorGroup, LogFile
from app.models.insight import GroupInsight
from app.models.report import IncidentReport

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


async def generate_report(session: AsyncSession, analysis: Analysis) -> IncidentReport:
    """Build (or rebuild) the incident report for a completed analysis."""
    log_file = await session.get(LogFile, analysis.log_file_id)
    groups = list(
        (
            await session.execute(
                select(ErrorGroup)
                .where(ErrorGroup.analysis_id == analysis.id)
                .order_by(ErrorGroup.count.desc())
            )
        ).scalars()
    )
    insights = {
        i.group_id: i
        for i in (
            await session.execute(
                select(GroupInsight).where(
                    GroupInsight.group_id.in_([g.id for g in groups])
                )
            )
        ).scalars()
    }

    title = _title(groups, log_file.filename)
    markdown = _render(analysis, log_file, groups, insights, title)

    existing = (
        await session.execute(
            select(IncidentReport).where(IncidentReport.analysis_id == analysis.id)
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.title = title
        existing.markdown = markdown
        await session.flush()
        return existing

    report = IncidentReport(
        analysis_id=analysis.id, user_id=analysis.user_id, title=title, markdown=markdown
    )
    session.add(report)
    await session.flush()
    return report


def _title(groups: list[ErrorGroup], filename: str) -> str:
    if not groups:
        return f"Incident report — {filename} (no errors detected)"
    top = min(groups, key=lambda g: _SEVERITY_ORDER.get(g.severity.value, 9))
    return f"Incident report — {top.severity.value.title()}: {filename}"


def _render(analysis, log_file, groups, insights, title) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# {title}",
        "",
        f"*Generated {now} · source `{log_file.filename}` · "
        f"{analysis.total_lines:,} lines, {analysis.error_lines:,} errors, "
        f"{analysis.group_count} distinct groups.*",
        "",
        "## Summary",
        "",
        _summary(groups, insights),
        "",
        "## Impact",
        "",
        f"- **{analysis.error_lines:,}** error-level lines across **{analysis.group_count}** "
        f"distinct problems.",
        f"- Severity spread: {_severity_breakdown(groups)}.",
        "",
        "## Findings",
        "",
    ]
    for i, group in enumerate(groups, 1):
        lines.extend(_finding(i, group, insights.get(group.id)))
    lines.extend(["## Prevention", "", _prevention(groups, insights), ""])
    return "\n".join(lines)


def _summary(groups, insights) -> str:
    if not groups:
        return "No warning- or error-level entries were found in this log."
    top = groups[0]
    insight = insights.get(top.id)
    if insight:
        p = insight.payload
        return (
            f"The dominant issue is **{p['error_type']}** ({top.count} occurrences): "
            f"{p['root_cause']}"
        )
    return f"The most frequent issue occurred {top.count} times: `{top.template}`."


def _severity_breakdown(groups) -> str:
    counts: dict[str, int] = {}
    for g in groups:
        counts[g.severity.value] = counts.get(g.severity.value, 0) + 1
    return ", ".join(f"{n} {sev}" for sev, n in sorted(counts.items())) or "none"


def _finding(index, group, insight) -> list[str]:
    header = f"### {index}. "
    if insight:
        p = insight.payload
        out = [
            header + f"{p['error_type']} — {group.severity.value} ({group.count}×)",
            "",
            f"**Root cause:** {p['root_cause']}",
            "",
            f"**Explanation:** {p['explanation']}",
            "",
            f"**Suggested fix:** {p['suggested_fix']}",
            "",
        ]
        commands = suggest_commands(p["error_type"])
        if commands:
            out.append("**Diagnostic commands (read-only):**")
            out.append("")
            out.append("```bash")
            out.extend(f"{c['command']}  # {c['description']}" for c in commands)
            out.append("```")
            out.append("")
    else:
        out = [
            header + f"{group.template} — {group.severity.value} ({group.count}×)",
            "",
            "_No AI insight available for this group._",
            "",
        ]
    if group.sample_lines:
        out.extend(["<details><summary>Sample lines</summary>", "", "```",
                    *group.sample_lines[:3], "```", "", "</details>", ""])
    return out


def _prevention(groups, insights) -> str:
    tips = []
    for group in groups[:3]:
        insight = insights.get(group.id)
        if insight:
            tips.append(f"- Address **{insight.payload['error_type']}**: "
                        f"{insight.payload['suggested_fix']}")
    return "\n".join(tips) if tips else "- Review the findings above and add monitoring/alerts."
