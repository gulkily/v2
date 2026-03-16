from __future__ import annotations

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
