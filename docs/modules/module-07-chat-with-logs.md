# Module 7 — Chat With Logs / RAG (Phase 5)

> **Status:** ✅ Built (2026-07-18) · 74/74 backend tests + frontend build verified
> Depends on: Modules 4–6 · Delivers AI Phase: 5 (AI chat with uploaded logs)

## As built — deviations from plan & key notes

- **Refusal in code, not just prompt**: if retrieval scores < threshold, the pipeline streams
  "I don't see anything about that in this log" **without calling the LLM at all** — asserted
  in tests via the mock's call counter. The prompt's grounding rule is the second defense line.
- **Lexical-first hybrid retrieval** (deviation worth understanding): bag-of-words cosine
  drowns rare error terms under repeated noise lines in 40-line chunks, so query-term coverage
  (with prefix matching as crude stemming) is the primary signal and cosine the tiebreaker.
  With the production sentence-transformer embedder, cosine carries real semantics again.
- **Ephemeral per-request index** instead of persisted chunk vectors: at the 2000-chunk cap
  this is milliseconds with hashing, one message's latency budget with ST. Persisting chunks
  in Qdrant is the documented optimization once usage justifies it.
- **Log-aware chunking**: overlapping line windows (40/10) with line-number provenance →
  citations like [lines 120-160] that the UI renders as evidence. Stride AND window widen
  together on huge files so coverage stays gap-free (a test caught the gap bug).
- **SSE via fetch + ReadableStream** on the frontend — EventSource can't send Authorization
  headers, a classic SSE gotcha now documented in code.
- **One conversation per (user, log file)** in v1; the user message is committed before
  streaming starts so it survives a mid-stream crash.
- Two live bugs caught by tests this module: variable shadowing in the chunker (`window`),
  and tail-gap coverage under widened stride.

## Goal

Analyses answer the questions we predicted; chat answers the ones we didn't. "What happened
between 10:12 and 10:15?", "which service failed first?" — retrieval-augmented generation over
the user's own log entries.

## What gets built

- [x] Log-aware chunking: overlapping line windows with line provenance + huge-file stride cap
- [x] Hybrid retrieval: query-term coverage (prefix-matched, stopword-filtered) + cosine
- [x] `Conversation` + `Message` models (migration 004); one conversation per (user, file)
- [x] `POST /logs/{id}/chat` streaming SSE + `GET /logs/{id}/chat` history
- [x] Grounding: code-level refusal below score threshold + prompt citation rules
- [x] Injection guards on chat: chunks and question both scrubbed + fenced
- [x] Chat UI: streamed tokens, citation footers, history restore, chat button on dashboard
- [x] Tests: chunking/retrieval units + 5 SSE integration flows (grounding, persistence,
      refusal-without-LLM-call, 503 when AI off, cross-user 404)

## Key concepts you'll learn

RAG architecture end-to-end; why chunking strategy dominates RAG quality; hybrid retrieval
(semantic + structured filters); SSE streaming through FastAPI; grounding and citation as
hallucination defense; conversation memory windows and token budgets.

## Planned files

`app/ai/rag/chunking.py`, `app/ai/rag/retriever.py`, `app/ai/pipelines/chat.py`,
`app/models/conversation.py`, `app/api/v1/chat.py`, `frontend/src/pages/Chat.tsx`

## Acceptance criteria (demo)

Ask "what happened between 10:12 and 10:15?" on the sample log → streamed answer citing the
actual timeout lines; ask about something absent → the model says it isn't in the log.
