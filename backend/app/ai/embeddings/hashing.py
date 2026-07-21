"""Hashing embedder: deterministic bag-of-words vectors, zero dependencies.

Not a semantic model — it measures TOKEN OVERLAP via the hashing trick (each
token hashes to a bucket; vector = normalized bucket counts). For normalized
error templates that's surprisingly effective ("connection timeout postgres"
vs "timeout connecting to postgres" share buckets), and it's exactly what
tests need: deterministic, instant, no torch. Production uses sentence
transformers via the same interface.
"""

import hashlib
import math
import re

_TOKEN = re.compile(r"[a-z]{2,}")


class HashingEmbedder:
    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]

    def _one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in _TOKEN.findall(text.lower()):
            bucket = int.from_bytes(hashlib.sha1(token.encode()).digest()[:4], "big") % self.dim  # noqa: S324
            vec[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
