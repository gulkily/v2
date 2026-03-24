from __future__ import annotations

import hashlib
import hmac
import os
import time
from email.utils import formatdate
from http.cookies import SimpleCookie

from forum_core.identity import normalize_fingerprint


IDENTITY_HINT_COOKIE_NAME = "forum_identity_hint"
IDENTITY_HINT_COOKIE_VERSION = "v1"
IDENTITY_HINT_COOKIE_MAX_AGE = 60 * 60 * 24 * 30


def identity_hint_secret(env: dict[str, str] | None = None) -> str:
    source_env = os.environ if env is None else env
    return source_env.get("FORUM_IDENTITY_HINT_SECRET", "").strip()


def _signature_payload(*, fingerprint: str, expires_at: int) -> bytes:
    return f"{IDENTITY_HINT_COOKIE_VERSION}|{fingerprint.lower()}|{expires_at}".encode("ascii")


def build_identity_hint_cookie_value(
    fingerprint: str,
    *,
    secret: str,
    now: int | None = None,
    max_age: int = IDENTITY_HINT_COOKIE_MAX_AGE,
) -> str:
    normalized = normalize_fingerprint(fingerprint).lower()
    issued_at = int(time.time() if now is None else now)
    expires_at = issued_at + max_age
    signature = hmac.new(
        secret.encode("utf-8"),
        _signature_payload(fingerprint=normalized, expires_at=expires_at),
        hashlib.sha256,
    ).hexdigest()
    return f"{IDENTITY_HINT_COOKIE_VERSION}.{normalized}.{expires_at}.{signature}"


def validate_identity_hint_cookie_value(
    raw_value: str | None,
    *,
    secret: str,
    now: int | None = None,
) -> str | None:
    if not raw_value or not secret:
        return None
    parts = raw_value.split(".")
    if len(parts) != 4:
        return None
    version, fingerprint, expires_at_text, signature = parts
    if version != IDENTITY_HINT_COOKIE_VERSION:
        return None
    try:
        normalized = normalize_fingerprint(fingerprint).lower()
        expires_at = int(expires_at_text)
    except (ValueError, TypeError):
        return None
    if expires_at < int(time.time() if now is None else now):
        return None
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        _signature_payload(fingerprint=normalized, expires_at=expires_at),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return None
    return normalized


def build_set_identity_hint_cookie_header(
    fingerprint: str,
    *,
    secret: str,
    now: int | None = None,
    max_age: int = IDENTITY_HINT_COOKIE_MAX_AGE,
) -> str:
    cookie = SimpleCookie()
    cookie[IDENTITY_HINT_COOKIE_NAME] = build_identity_hint_cookie_value(
        fingerprint,
        secret=secret,
        now=now,
        max_age=max_age,
    )
    morsel = cookie[IDENTITY_HINT_COOKIE_NAME]
    morsel["path"] = "/"
    morsel["max-age"] = str(max_age)
    morsel["secure"] = True
    morsel["httponly"] = True
    morsel["samesite"] = "Lax"
    return morsel.OutputString()


def build_clear_identity_hint_cookie_header() -> str:
    cookie = SimpleCookie()
    cookie[IDENTITY_HINT_COOKIE_NAME] = ""
    morsel = cookie[IDENTITY_HINT_COOKIE_NAME]
    morsel["path"] = "/"
    morsel["max-age"] = "0"
    morsel["expires"] = formatdate(0, usegmt=True)
    morsel["secure"] = True
    morsel["httponly"] = True
    morsel["samesite"] = "Lax"
    return morsel.OutputString()
