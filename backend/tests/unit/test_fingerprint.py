"""Fingerprint stability: the property that makes grouping work."""

from app.parsing.fingerprint import fingerprint, template_of


def test_variable_parts_are_normalized() -> None:
    template = template_of("Connection timeout for user 8231 from 10.0.3.7:5432")

    assert "<n>" in template
    assert "<ip>" in template
    assert "8231" not in template


def test_same_error_different_noise_same_fingerprint() -> None:
    fp1, _ = fingerprint("error", "Timeout for user 8231 from 10.0.3.7 at 2026-07-15 10:12:14")
    fp2, _ = fingerprint("error", "Timeout for user 9440 from 10.9.1.2 at 2026-07-15 11:03:59")

    assert fp1 == fp2


def test_different_errors_different_fingerprints() -> None:
    fp1, _ = fingerprint("error", "Database connection timeout")
    fp2, _ = fingerprint("error", "Disk quota exceeded")

    assert fp1 != fp2


def test_level_is_part_of_identity() -> None:
    fp_err, _ = fingerprint("error", "Connection timeout")
    fp_warn, _ = fingerprint("warning", "Connection timeout")

    assert fp_err != fp_warn  # same text at error vs warning = different problems


def test_uuids_paths_and_quotes_normalized() -> None:
    template = template_of(
        "Job 4f9c2d1e-8b3a-4c5d-9e6f-1a2b3c4d5e6f failed reading /var/data/chunk.bin: 'EOF'"
    )

    assert "<uuid>" in template
    assert "<path>" in template
    assert "<str>" in template


def test_fingerprint_is_deterministic() -> None:
    results = {fingerprint("error", "Connection refused to PostgreSQL")[0] for _ in range(50)}
    assert len(results) == 1
