"""Multi-agent investigation: planner → investigators → verifier, budgeted.

When multi-agent is worth it: complex, multi-service incidents where one prompt
can't hold the whole causal chain. When it ISN'T (the honest case): most
single-error analyses — those are already handled in M4 for a fraction of the
cost. The orchestrator therefore has HARD budgets (max steps, wall clock) and
falls back to the single-shot M4 result when agents disagree or run out.
"""
