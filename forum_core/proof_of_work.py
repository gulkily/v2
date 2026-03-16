from __future__ import annotations

import hashlib
import os
from pathlib import Path

from forum_core.identity import build_bootstrap_record_id, build_identity_id


POW_FIRST_POST_FLAG_ENV = "FORUM_ENABLE_FIRST_POST_POW"
POW_FIRST_POST_DIFFICULTY_ENV = "FORUM_FIRST_POST_POW_DIFFICULTY"
DEFAULT_POW_DIFFICULTY = 18


def first_post_pow_enabled(env: dict[str, str] | None = None) -> bool:
    source_env = env or os.environ
    raw_value = source_env.get(POW_FIRST_POST_FLAG_ENV, "").strip().lower()
    return raw_value in {"1", "true", "yes", "on"}


def first_post_pow_difficulty(env: dict[str, str] | None = None) -> int:
    source_env = env or os.environ
    raw_value = source_env.get(POW_FIRST_POST_DIFFICULTY_ENV, "").strip()
    if not raw_value:
        return DEFAULT_POW_DIFFICULTY
    try:
        difficulty = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{POW_FIRST_POST_DIFFICULTY_ENV} must be a decimal integer") from exc
    if difficulty < 1:
        raise ValueError(f"{POW_FIRST_POST_DIFFICULTY_ENV} must be at least 1")
    return difficulty


def pow_required_for_signed_post(*, repo_root: Path, signer_fingerprint: str) -> bool:
    identity_id = build_identity_id(signer_fingerprint)
    bootstrap_path = repo_root / "records" / "identity" / f"{build_bootstrap_record_id(identity_id)}.txt"
    return not bootstrap_path.exists()


def build_pow_message(*, signer_fingerprint: str, post_id: str, nonce: str, difficulty: int) -> bytes:
    return (
        f"forum-pow-v1\n"
        f"{signer_fingerprint.strip().upper()}\n"
        f"{post_id.strip()}\n"
        f"{difficulty}\n"
        f"{nonce.strip().lower()}\n"
    ).encode("ascii")


def count_leading_zero_bits(digest: bytes) -> int:
    count = 0
    for byte in digest:
        if byte == 0:
            count += 8
            continue
        return count + (8 - byte.bit_length())
    return count


def extract_post_id(payload_text: str) -> str:
    for line in payload_text.splitlines():
        if not line.strip():
            break
        if line.startswith("Post-ID: "):
            post_id = line.split(": ", 1)[1].strip()
            if post_id:
                return post_id
            break
    raise ValueError("payload is missing Post-ID")


def verify_first_post_pow_stamp(
    *,
    payload_text: str,
    signer_fingerprint: str,
    stamp: str,
    difficulty: int,
) -> None:
    normalized_stamp = stamp.strip()
    if not normalized_stamp:
        raise ValueError("pow_stamp is required")
    if ":" in normalized_stamp:
        version, separator, nonce = normalized_stamp.partition(":")
        if separator != ":" or version != "v1" or not nonce:
            raise ValueError("pow_stamp must use the form v1:<nonce>")
    else:
        nonce = normalized_stamp
    if not nonce or any(character not in "0123456789abcdefABCDEF" for character in nonce):
        raise ValueError("pow_stamp nonce must be hexadecimal")

    digest = hashlib.sha256(
        build_pow_message(
            signer_fingerprint=signer_fingerprint,
            post_id=extract_post_id(payload_text),
            nonce=nonce,
            difficulty=difficulty,
        )
    ).digest()
    if count_leading_zero_bits(digest) < difficulty:
        raise ValueError("pow_stamp does not satisfy the configured difficulty")
