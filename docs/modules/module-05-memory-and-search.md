# Module 5 — Memory & Similar-Incident Search (Phase 4)

> **Status:** ✅ Built (2026-07-18) · 64/64 total tests passing
> Depends on: Module 4 · Delivers AI Phase: 4 (similar incident search)

## As built — deviations from plan & key notes

- **Two-backend embedding seam**: `HashingEmbedder` (deterministic bag-of-words hashing trick,
  zero deps — default for tests/dev) and `SentenceTransformerEmbedder` (semantic, lazy torch
  import — Docker/prod via `APP_EMBEDDING_BACKEND=sentence-transformers`). Same interface, and
  for *normalized error templates* token overlap is a surprisingly strong baseline.
- **Qdrant via REST (httpx)**, no qdrant-client dependency — consistent with the OpenAI choice.
  The `user_id` payload filter is applied SERVER-side in the search body; the in-memory test
  store enforces the same rule, and isolation is asserted in integration tests.
- **Indexing failure never fails the analysis** (same degradation contract as AI insights).
- Similar endpoint searches the **top 3 groups** of an analysis and merges/dedupes matches,
  excluding the analysis itself; threshold 0.4 keeps noise out.
- Deferred: backfill task for pre-existing analyses (trivial once needed), similarity-score
  display tuning after real-model calibration.

## Goal

"Have we seen this before?" is the first question every on-call asks. Past analyses become
searchable memory: embed error groups, store vectors in Qdrant, retrieve similar incidents with
their past root causes and fixes.

## What gets built

- [x] Qdrant container in compose (healthchecked, persistent volume)
- [x] Embedding seam: hashing (test/dev) + sentence-transformers (prod, lazy import)
- [x] Index on analysis completion: template → vector + payload (user_id, analysis, severity)
- [x] `GET /analyses/{id}/similar` — server-side user filter = tenant isolation
- [x] Threshold (0.4) + cosine score surfaced in responses
- [x] Analysis history endpoint: `GET /analyses` paginated, newest first, with filename
- [ ] Backfill task for pre-existing analyses (deferred — trivial when needed)
- [x] Deterministic embedding tests + cross-analysis/-user integration tests

## Key concepts you'll learn

Embeddings and cosine similarity in practice; vector DB payload filtering (why FAISS alone
can't do per-user isolation); chunking vs whole-document embedding tradeoffs; local models vs
API embeddings (cost, latency, privacy); when semantic search beats keyword search and when it
doesn't.

## Planned files

`app/ai/embeddings.py`, `app/ai/vectorstore.py`, `app/services/similarity.py`,
`app/api/v1/history.py`, `tests/unit/test_similarity.py`

## Acceptance criteria (demo)

Analyze two logs with related DB failures on different days → the second analysis links to the
first as a similar incident with a similarity score; another user's incidents never appear.
