"""Sentence-transformers embedder (production; requires torch — Docker only).

Lazy import: this module only pulls the heavy dependency when instantiated,
so the API process and test suite never pay for it.
"""

import asyncio


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer  # heavy — lazy on purpose

        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # encode() is CPU-bound sync work — off the event loop with to_thread.
        vectors = await asyncio.to_thread(self._model.encode, texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vectors]
