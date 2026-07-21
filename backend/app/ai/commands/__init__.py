"""Remediation command suggestion: allow-listed templates, parameter-validated.

Security model (ADR-worthy): the LLM never emits free-form shell. It picks a
template ID from a curated catalog and supplies typed parameters; we render the
final string from OUR template with OUR validation. A model told to output
`rm -rf /` simply has no template that produces it. This is deny-by-default,
the same principle as M4's command filter but stronger — allow-listing the
STRUCTURE, not just filtering the output.
"""

from app.ai.commands.catalog import CATALOG, CommandTemplate, render_command

__all__ = ["CATALOG", "CommandTemplate", "render_command"]
