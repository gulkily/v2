from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


IDENTITY_SCHEME = "openpgp"


@dataclass(frozen=True)
class IdentityBootstrap:
    record_id: str
    identity_id: str
    signer_fingerprint: str
    bootstrap_post_id: str
    bootstrap_thread_id: str
    public_key_text: str
    path: Path


@dataclass(frozen=True)
class ProfileSummary:
    identity_id: str
    signer_fingerprint: str
    bootstrap_record_id: str
    bootstrap_post_id: str
    bootstrap_thread_id: str
    bootstrap_path: str
    post_ids: tuple[str, ...]
    thread_ids: tuple[str, ...]
    public_key_text: str


def normalize_fingerprint(fingerprint: str) -> str:
    normalized = "".join(character for character in fingerprint.strip().upper() if character.isalnum())
    if not normalized:
        raise ValueError("fingerprint must not be blank")
    return normalized


def build_identity_id(fingerprint: str) -> str:
    return f"{IDENTITY_SCHEME}:{normalize_fingerprint(fingerprint).lower()}"


def build_bootstrap_record_id(identity_id: str) -> str:
    scheme, separator, value = identity_id.partition(":")
    if separator != ":" or not scheme or not value:
        raise ValueError("identity_id must use the form <scheme>:<value>")
    return f"identity-{scheme}-{value}"


def identity_slug(identity_id: str) -> str:
    return build_bootstrap_record_id(identity_id).removeprefix("identity-")


def identity_id_from_slug(slug: str) -> str:
    scheme, separator, value = slug.partition("-")
    if separator != "-" or not scheme or not value:
        raise ValueError("identity slug must use the form <scheme>-<value>")
    return f"{scheme}:{value}"


def short_identity_label(fingerprint: str) -> str:
    normalized = normalize_fingerprint(fingerprint)
    if len(normalized) <= 16:
        return normalized
    return f"{normalized[:16]}.."


@lru_cache(maxsize=256)
def fingerprint_from_public_key_text(public_key_text: str) -> str:
    try:
        public_key_text.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("public key text must be ASCII") from exc

    with tempfile.TemporaryDirectory(prefix="forum-key-show-", dir="/tmp") as tempdir:
        temp_path = Path(tempdir)
        homedir = temp_path / "gnupg-home"
        homedir.mkdir(mode=0o700)

        public_key_path = temp_path / "public.asc"
        public_key_path.write_text(public_key_text, encoding="ascii")

        result = subprocess.run(
            [
                "gpg",
                "--homedir",
                str(homedir),
                "--batch",
                "--with-colons",
                "--show-keys",
                str(public_key_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise ValueError("public key fingerprint could not be derived")

        for line in result.stdout.splitlines():
            if line.startswith("fpr:"):
                fields = line.split(":")
                if len(fields) > 9 and fields[9]:
                    return normalize_fingerprint(fields[9])

    raise ValueError("public key fingerprint could not be derived")


def fingerprint_from_public_key_path(public_key_path: Path) -> str:
    return fingerprint_from_public_key_text(public_key_path.read_text(encoding="ascii"))


def parse_identity_bootstrap_text(raw_text: str, *, source_path: Path | None = None) -> IdentityBootstrap:
    header_text, separator, body_text = raw_text.partition("\n\n")
    if not separator:
        raise ValueError("identity bootstrap text is missing header/body separator")

    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        if ": " not in line:
            raise ValueError(f"invalid identity bootstrap header line: {line!r}")
        key, value = line.split(": ", 1)
        headers[key] = value.strip()

    record_id = headers.get("Post-ID")
    identity_id = headers.get("Identity-ID")
    signer_fingerprint = headers.get("Signer-Fingerprint")
    bootstrap_post_id = headers.get("Bootstrap-By-Post")
    bootstrap_thread_id = headers.get("Bootstrap-By-Thread")
    public_key_text = body_text.rstrip("\n")

    if not record_id or not identity_id or not signer_fingerprint:
        raise ValueError("identity bootstrap text is missing required identity headers")
    if not bootstrap_post_id or not bootstrap_thread_id:
        raise ValueError("identity bootstrap text is missing bootstrap source headers")
    if not public_key_text:
        raise ValueError("identity bootstrap body must contain an ASCII-armored public key")

    return IdentityBootstrap(
        record_id=record_id,
        identity_id=identity_id,
        signer_fingerprint=normalize_fingerprint(signer_fingerprint),
        bootstrap_post_id=bootstrap_post_id,
        bootstrap_thread_id=bootstrap_thread_id,
        public_key_text=public_key_text,
        path=source_path or Path("<request>"),
    )


def parse_identity_bootstrap(path: Path) -> IdentityBootstrap:
    return parse_identity_bootstrap_text(path.read_text(encoding="ascii"), source_path=path)


def load_identity_bootstraps(identity_dir: Path) -> list[IdentityBootstrap]:
    return [parse_identity_bootstrap(path) for path in sorted(identity_dir.glob("*.txt"))]


def index_identity_bootstraps(bootstraps: list[IdentityBootstrap]) -> dict[str, IdentityBootstrap]:
    return {bootstrap.identity_id: bootstrap for bootstrap in bootstraps}


def build_bootstrap_payload(
    *,
    identity_id: str,
    signer_fingerprint: str,
    bootstrap_post_id: str,
    bootstrap_thread_id: str,
    public_key_text: str,
) -> tuple[str, str]:
    normalized_identity_id = build_identity_id(signer_fingerprint)
    if identity_id != normalized_identity_id:
        raise ValueError("identity_id must match the signer fingerprint")

    normalized_public_key = public_key_text.rstrip("\n")
    if not normalized_public_key:
        raise ValueError("public key text must not be blank")
    try:
        normalized_public_key.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("public key text must be ASCII") from exc

    record_id = build_bootstrap_record_id(identity_id)
    payload_lines = [
        f"Post-ID: {record_id}",
        "Board-Tags: identity",
        "Subject: identity bootstrap",
        f"Identity-ID: {identity_id}",
        f"Signer-Fingerprint: {normalize_fingerprint(signer_fingerprint)}",
        f"Bootstrap-By-Post: {bootstrap_post_id}",
        f"Bootstrap-By-Thread: {bootstrap_thread_id}",
        "",
        normalized_public_key,
    ]
    return record_id, "\n".join(payload_lines) + "\n"


def render_profile_summary_text(summary: ProfileSummary) -> str:
    lines = [
        f"Identity-ID: {summary.identity_id}",
        f"Signer-Fingerprint: {summary.signer_fingerprint}",
        f"Bootstrap-Record-ID: {summary.bootstrap_record_id}",
        f"Bootstrap-Path: {summary.bootstrap_path}",
        f"Bootstrap-By-Post: {summary.bootstrap_post_id}",
        f"Bootstrap-By-Thread: {summary.bootstrap_thread_id}",
        f"Post-Count: {len(summary.post_ids)}",
        f"Thread-Count: {len(summary.thread_ids)}",
        "",
        "Posts:",
    ]
    lines.extend(summary.post_ids)
    lines.extend(["", "Public-Key:", summary.public_key_text])
    return "\n".join(lines) + "\n"
