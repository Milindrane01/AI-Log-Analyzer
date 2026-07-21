"""AI analysis stage: enrich top error groups with insights.

Cost + resilience rules:
- Only the top N groups by count get AI (settings.ai_max_groups_per_analysis).
- Fingerprint cache: same user + same fingerprint → reuse the stored insight,
  zero tokens. (212 identical timeouts → one LLM call, ever.)
- Per-group failures degrade gracefully: the analysis still completes; a group
  without an insight is a UI state, not an error.
"""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.guards.injection import filter_commands
from app.ai.prompts.analysis import PROMPT_VERSION
from app.ai.providers.base import InsightRequest, LLMError, LLMProvider
from app.models import ErrorGroup, Severity
from app.models.insight import GroupInsight

log = structlog.get_logger()

_SEVERITY_MAP = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
}


async def enrich_groups(
    session: AsyncSession,
    provider: LLMProvider,
    groups: list[ErrorGroup],
    user_id: str,
    detected_format: str | None,
    max_groups: int,
) -> int:
    """Attach insights to the top-N groups. Returns number of insights written."""
    written = 0
    top = sorted(groups, key=lambda g: g.count, reverse=True)[:max_groups]
    for group in top:
        try:
            written += await _enrich_one(session, provider, group, user_id, detected_format)
        except Exception:
            # One bad group must not sink the batch — log and continue.
            log.warning("insight_failed", group_id=group.id, exc_info=True)
    return written


async def _enrich_one(
    session: AsyncSession,
    provider: LLMProvider,
    group: ErrorGroup,
    user_id: str,
    detected_format: str | None,
) -> int:
    cached = await session.execute(
        select(GroupInsight)
        .where(GroupInsight.user_id == user_id, GroupInsight.fingerprint == group.fingerprint)
        .limit(1)
    )
    prior = cached.scalar_one_or_none()
    if prior is not None:
        session.add(
            GroupInsight(
                group_id=group.id,
                user_id=user_id,
                fingerprint=group.fingerprint,
                payload=prior.payload,
                model=prior.model,
                prompt_version=prior.prompt_version,
                from_cache=True,
            )
        )
        _apply_severity(group, prior.payload.get("severity"))
        await session.flush()
        log.info("insight_cache_hit", group_id=group.id, fingerprint=group.fingerprint[:12])
        return 1

    try:
        response = await provider.analyze_group(
            InsightRequest(
                level=group.level,
                template=group.template,
                count=group.count,
                sample_lines=group.sample_lines or [],
                detected_format=detected_format,
            )
        )
    except LLMError as exc:
        log.warning("llm_call_failed", group_id=group.id, error=str(exc))
        return 0

    result = response.result
    # Guard layer 3: deny-by-default command filtering on the way IN to storage.
    result.recommended_commands = filter_commands(result.recommended_commands)

    session.add(
        GroupInsight(
            group_id=group.id,
            user_id=user_id,
            fingerprint=group.fingerprint,
            payload=result.model_dump(),
            model=response.usage.model,
            prompt_version=PROMPT_VERSION,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )
    )
    _apply_severity(group, result.severity)
    await session.flush()
    return 1


def _apply_severity(group: ErrorGroup, severity: str | None) -> None:
    """AI refines the M3 level-based severity heuristic (content > level)."""
    if severity in _SEVERITY_MAP:
        group.severity = _SEVERITY_MAP[severity]
