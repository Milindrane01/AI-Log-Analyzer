"""AI layer: providers, prompts, guards, pipelines.

Design rules for this package:
1. Everything behind interfaces — no OpenAI SDK types leak past providers/.
2. Log content is UNTRUSTED INPUT (attacker-controlled). guards/ is not optional.
3. Every output is schema-validated before persistence. Free text is a bug.
"""
