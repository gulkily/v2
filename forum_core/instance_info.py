from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from forum_core.moderation import moderator_fingerprint_allowlist


@dataclass(frozen=True)
class TrackedInstanceInfo:
    instance_name: str
    admin_name: str
    admin_contact: str
    retention_policy: str
    install_date: str
    summary: str
    path: Path


@dataclass(frozen=True)
class InstanceInfo:
    instance_name: str | None
    admin_name: str | None
    admin_contact: str | None
    retention_policy: str | None
    install_date: str | None
    summary: str | None
    moderation_settings: str
    commit_id: str | None
    commit_date: str | None
    source_path: Path


def instance_info_path(repo_root: Path) -> Path:
    return repo_root / "records" / "instance" / "public.txt"


def parse_instance_info_text(raw_text: str, *, source_path: Path | None = None) -> TrackedInstanceInfo:
    header_text, separator, body_text = raw_text.partition("\n\n")
    if not separator:
        raise ValueError("instance info text is missing header/body separator")

    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        if ": " not in line:
            raise ValueError(f"invalid instance info header line: {line!r}")
        key, value = line.split(": ", 1)
        headers[key] = value.strip()

    def require_header(name: str) -> str:
        value = headers.get(name, "").strip()
        if not value:
            raise ValueError(f"instance info text is missing required header: {name}")
        return value

    return TrackedInstanceInfo(
        instance_name=require_header("Instance-Name"),
        admin_name=require_header("Admin-Name"),
        admin_contact=require_header("Admin-Contact"),
        retention_policy=require_header("Retention-Policy"),
        install_date=require_header("Install-Date"),
        summary=body_text.rstrip("\n"),
        path=source_path or Path("<instance-info>"),
    )


def load_tracked_instance_info(repo_root: Path) -> TrackedInstanceInfo | None:
    path = instance_info_path(repo_root)
    if not path.exists():
        return None
    return parse_instance_info_text(path.read_text(encoding="utf-8"), source_path=path)


def resolve_commit_id(repo_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def resolve_commit_date(repo_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "log", "-1", "--format=%cI"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def describe_moderation_settings() -> str:
    allowlist = moderator_fingerprint_allowlist()
    if not allowlist:
        return "Signed moderation is enabled, but no moderator fingerprints are configured."
    count = len(allowlist)
    return f"Signed moderation is enabled for {count} configured moderator{'s' if count != 1 else ''}."


def render_public_value(value: str | None) -> str:
    stripped = (value or "").strip()
    return stripped if stripped else "Not published."


def load_instance_info(repo_root: Path) -> InstanceInfo:
    tracked = load_tracked_instance_info(repo_root)
    source_path = tracked.path if tracked is not None else instance_info_path(repo_root)
    return InstanceInfo(
        instance_name=tracked.instance_name if tracked else None,
        admin_name=tracked.admin_name if tracked else None,
        admin_contact=tracked.admin_contact if tracked else None,
        retention_policy=tracked.retention_policy if tracked else None,
        install_date=tracked.install_date if tracked else None,
        summary=tracked.summary if tracked and tracked.summary else None,
        moderation_settings=describe_moderation_settings(),
        commit_id=resolve_commit_id(repo_root),
        commit_date=resolve_commit_date(repo_root),
        source_path=source_path,
    )
