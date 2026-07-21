"""Deterministic log parsing: format detection, parsing, fingerprinting.

No AI in this package — everything here is reproducible and unit-testable.
This is deliberate: the LLM (M4) receives clean, grouped, deduplicated errors,
which is the project's main cost AND quality lever.
"""
