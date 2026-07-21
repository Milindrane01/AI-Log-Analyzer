"""RAG over raw log files: chunking + retrieval. Chunking strategy dominates
RAG quality — ours is log-aware (line windows with overlap, line-number
provenance for citations), not naive character splitting."""
