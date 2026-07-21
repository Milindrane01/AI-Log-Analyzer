"""Security primitives: hashing and tokens. Pure unit tests, no app needed."""

import pytest

from app.core.config import Settings
from app.core.security import (
    TokenError,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)

settings = Settings(_env_file=None)


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("correct horse battery staple")

    assert hashed != "correct horse battery staple"  # never plaintext
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_same_password_hashes_differently() -> None:
    # Unique salt per hash: identical passwords must not produce identical
    # hashes (rainbow-table defense).
    assert hash_password("pw-example-123") != hash_password("pw-example-123")


def test_token_roundtrip() -> None:
    token = create_token(settings, "user-1", "access")
    payload = decode_token(settings, token, expected_type="access")

    assert payload["sub"] == "user-1"
    assert payload["jti"]  # unique id present for future revocation


def test_refresh_token_rejected_as_access() -> None:
    token = create_token(settings, "user-1", "refresh")

    with pytest.raises(TokenError, match="expected access"):
        decode_token(settings, token, expected_type="access")


def test_tampered_token_rejected() -> None:
    token = create_token(settings, "user-1", "access")
    tampered = token[:-4] + "AAAA"

    with pytest.raises(TokenError):
        decode_token(settings, tampered, expected_type="access")


def test_token_signed_with_other_key_rejected() -> None:
    other = Settings(_env_file=None, jwt_secret_key="a-completely-different-secret")
    token = create_token(other, "user-1", "access")

    with pytest.raises(TokenError):
        decode_token(settings, token, expected_type="access")
