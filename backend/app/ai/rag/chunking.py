"""Log-aware chunking: overlapping line windows with provenance.

Why line windows, not character splits: a log line is the atomic unit of
meaning; cutting mid-line destroys it. Overlap keeps multi-line events (stack
traces) intact in at least one chunk. Line ranges make citations possible —
the model can say "lines 120-160" and the UI can show them.
"""

from dataclasses import dataclass

WINDOW_LINES = 40
OVERLAP_LINES = 10
MAX_CHUNKS = 2000  # cap for very large files; stride widens beyond this
MAX_CHARS_PER_LINE = 500


@dataclass(slots=True)
class Chunk:
    start_line: int  # 1-based, inclusive
    end_line: int
    text: str


def chunk_lines(lines: list[str]) -> list[Chunk]:
    """Split log lines into overlapping windows; widen stride for huge files."""
    clean = [line.rstrip("\n")[:MAX_CHARS_PER_LINE] for line in lines]
    total = len(clean)
    if total == 0:
        return []

    stride = WINDOW_LINES - OVERLAP_LINES
    window = WINDOW_LINES
    # If the naive chunk count would blow the cap, widen stride AND window
    # together so coverage stays gap-free (coarser windows on huge files —
    # a documented recall/scale tradeoff).
    est = max(1, (total - OVERLAP_LINES) // stride)
    if est > MAX_CHUNKS:
        stride = max(stride, total // MAX_CHUNKS)
        window = stride + OVERLAP_LINES

    chunks: list[Chunk] = []
    start = 0
    while start < total:
        end = min(start + window, total)
        kept = [line for line in clean[start:end] if line.strip()]
        if kept:
            chunks.append(Chunk(start_line=start + 1, end_line=end, text="\n".join(kept)))
        if end >= total:
            break
        start += stride
    return chunks
