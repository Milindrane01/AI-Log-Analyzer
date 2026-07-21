"""Chunking + retrieval unit tests."""

from app.ai.embeddings.hashing import HashingEmbedder
from app.ai.rag.chunking import WINDOW_LINES, chunk_lines
from app.ai.rag.retriever import retrieve


def test_chunks_have_line_provenance_and_overlap() -> None:
    lines = [f"2026-07-15 10:00:{i:02d} INFO event number {i}\n" for i in range(100)]
    chunks = chunk_lines(lines)

    assert chunks[0].start_line == 1
    assert chunks[0].end_line == WINDOW_LINES
    # Overlap: second chunk starts before the first ends.
    assert chunks[1].start_line < chunks[0].end_line
    # Full coverage: last chunk reaches the last line.
    assert chunks[-1].end_line == 100


def test_empty_and_blank_files_yield_no_chunks() -> None:
    assert chunk_lines([]) == []
    assert chunk_lines(["\n", "   \n"]) == []


def test_huge_file_respects_chunk_cap() -> None:
    lines = [f"line {i}\n" for i in range(200_000)]
    chunks = chunk_lines(lines)

    assert len(chunks) <= 2100  # cap + tail tolerance
    assert chunks[-1].end_line == 200_000  # still covers the whole file


async def test_retrieval_finds_the_relevant_window() -> None:
    lines = [f"2026-07-15 10:00:{i:02d} INFO heartbeat ok\n" for i in range(60)]
    lines[42] = "2026-07-15 10:00:42 ERROR postgres connection timeout on primary\n"
    chunks = chunk_lines(lines)

    hits = await retrieve(HashingEmbedder(), chunks, "why did postgres time out?")

    assert hits, "expected a retrieval hit"
    top = hits[0]
    assert top.chunk.start_line <= 43 <= top.chunk.end_line  # the error line is inside
    assert "postgres connection timeout" in top.chunk.text


async def test_retrieval_returns_nothing_for_unrelated_query() -> None:
    lines = ["2026-07-15 10:00:00 INFO heartbeat ok\n"] * 50
    chunks = chunk_lines(lines)

    hits = await retrieve(HashingEmbedder(), chunks, "kubernetes ingress certificate renewal")

    assert hits == []  # below MIN_SCORE → pipeline will refuse instead of guessing
