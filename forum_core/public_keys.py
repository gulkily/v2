from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from forum_core.identity import fingerprint_from_public_key_text, normalize_fingerprint


@dataclass(frozen=True)
class StoredPublicKeyRef:
    fingerprint: str
    path: Path
    created: bool


def public_key_records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "public-keys"


def resolve_canonical_public_key_path(repo_root: Path, fingerprint: str) -> Path:
    normalized = normalize_fingerprint(fingerprint).lower()
    return public_key_records_dir(repo_root) / f"openpgp-{normalized}.asc"


def resolve_public_key_by_fingerprint(repo_root: Path, fingerprint: str) -> Path | None:
    path = resolve_canonical_public_key_path(repo_root, fingerprint)
    return path if path.exists() else None


def store_or_reuse_public_key(*, repo_root: Path, public_key_text: str) -> StoredPublicKeyRef:
    fingerprint = fingerprint_from_public_key_text(public_key_text)
    path = resolve_canonical_public_key_path(repo_root, fingerprint)
    created = not path.exists()
    if created:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(public_key_text, encoding="ascii")
    return StoredPublicKeyRef(
        fingerprint=fingerprint,
        path=path,
        created=created,
    )


def fingerprint_from_signature_path(signature_path: Path) -> str:
    result = subprocess.run(
        [
            "gpg",
            "--batch",
            "--list-packets",
            str(signature_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError("signature fingerprint could not be derived")

    for line in result.stdout.splitlines():
        marker = "(issuer fpr v4 "
        if marker in line:
            _, _, suffix = line.partition(marker)
            fingerprint, _, _ = suffix.partition(")")
            if fingerprint.strip():
                return normalize_fingerprint(fingerprint)

    raise ValueError("signature fingerprint could not be derived")


def resolve_public_key_from_signature(*, repo_root: Path, signature_path: Path | None) -> Path | None:
    if signature_path is None or not signature_path.exists():
        return None
    fingerprint = fingerprint_from_signature_path(signature_path)
    return resolve_public_key_by_fingerprint(repo_root, fingerprint)
