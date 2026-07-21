# ADR-003: Use Qdrant (server) instead of FAISS (library) for vectors

- **Status:** Accepted
- **Date:** 2026-07-16
- **Deciders:** TG

## Context

Similar-incident search (M5) and RAG chat (M7) need vector similarity search with per-user
isolation and persistence across restarts.

## Decision

Run Qdrant as a container alongside postgres/redis. Vectors carry payloads (user_id, severity,
timestamps) used as mandatory query filters — payload filtering is the tenant-isolation
mechanism.

## Alternatives considered

| Option | Why rejected |
|---|---|
| FAISS in-process | No persistence/ops story, no payload filtering (per-user isolation becomes manual bookkeeping), doesn't demonstrate production patterns |
| pgvector | Strong option (one less service); rejected to keep vector workload independently scalable and to gain first-class filtering/quantization — revisit trigger below |
| Pinecone / managed | Cost + external dependency for a portfolio project that must run locally |

## Consequences

One more container in compose/K8s. We gain real filtering, snapshots, and an ops story to
present. Revisit if: operational overhead outweighs benefits at our scale — pgvector is the
fallback and the migration seam is the `VectorStore` interface.
