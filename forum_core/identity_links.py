from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from forum_core.identity import build_identity_id, fingerprint_from_public_key_path, fingerprint_from_public_key_text


ALLOWED_IDENTITY_LINK_ACTIONS = ("rotate_key", "merge_identity")


@dataclass(frozen=True)
class IdentityLinkRecord:
    record_id: str
    action: str
    source_identity_id: str
    target_identity_id: str
    timestamp: str
    note: str
    path: Path
    target_public_key_text: str | None = None
    signature_path: Path | None = None
    public_key_path: Path | None = None
    signer_fingerprint: str | None = None
    identity_id: str | None = None


@dataclass(frozen=True)
class IdentityResolution:
    canonical_by_identity_id: dict[str, str]
    members_by_canonical_identity_id: dict[str, tuple[str, ...]]

    def canonical_identity_id(self, identity_id: str | None) -> str | None:
        if identity_id is None:
            return None
        return self.canonical_by_identity_id.get(identity_id)

    def member_identity_ids(self, identity_id: str | None) -> tuple[str, ...]:
        canonical_identity_id = self.canonical_identity_id(identity_id)
        if canonical_identity_id is None:
            return ()
        return self.members_by_canonical_identity_id.get(canonical_identity_id, ())


def identity_link_records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "identity-links"


def ensure_identity_id_text(identity_id: str, *, field_name: str) -> str:
    value = identity_id.strip()
    scheme, separator, token = value.partition(":")
    if separator != ":" or not scheme or not token:
        raise ValueError(f"{field_name} must use the form <scheme>:<value>")
    return f"{scheme}:{token}"


def ensure_timestamp_text(timestamp_text: str) -> str:
    try:
        datetime.strptime(timestamp_text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("Timestamp must use UTC ISO-8601 form YYYY-MM-DDTHH:MM:SSZ") from exc
    return timestamp_text


def parse_identity_link_text(raw_text: str, *, source_path: Path | None = None) -> IdentityLinkRecord:
    header_text, separator, body_text = raw_text.partition("\n\n")
    if not separator:
        raise ValueError("identity-link text is missing header/body separator")

    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        if ": " not in line:
            raise ValueError(f"invalid identity-link header line: {line!r}")
        key, value = line.split(": ", 1)
        headers[key] = value.strip()

    record_id = headers.get("Record-ID")
    action = (headers.get("Action") or "").strip().lower()
    source_identity_id = headers.get("Source-Identity-ID")
    target_identity_id = headers.get("Target-Identity-ID")
    timestamp = headers.get("Timestamp")

    if not record_id or not action or not source_identity_id or not target_identity_id or not timestamp:
        raise ValueError("identity-link text is missing required headers")
    if action not in ALLOWED_IDENTITY_LINK_ACTIONS:
        raise ValueError(f"unsupported identity-link action: {action}")

    normalized_source_identity_id = ensure_identity_id_text(source_identity_id, field_name="Source-Identity-ID")
    normalized_target_identity_id = ensure_identity_id_text(target_identity_id, field_name="Target-Identity-ID")
    if normalized_source_identity_id == normalized_target_identity_id:
        raise ValueError("Source-Identity-ID and Target-Identity-ID must differ")

    normalized_body = body_text.rstrip("\n")
    target_public_key_text = None
    note = normalized_body
    if action == "rotate_key":
        if not normalized_body:
            raise ValueError("rotate_key identity-link records must include the target public key in the body")
        target_public_key_text = normalized_body
        derived_target_identity_id = build_identity_id(fingerprint_from_public_key_text(target_public_key_text))
        if derived_target_identity_id != normalized_target_identity_id:
            raise ValueError("Target-Identity-ID must match the target public key in the body")
        note = ""

    return IdentityLinkRecord(
        record_id=record_id,
        action=action,
        source_identity_id=normalized_source_identity_id,
        target_identity_id=normalized_target_identity_id,
        timestamp=ensure_timestamp_text(timestamp),
        note=note,
        path=source_path or Path("<request>"),
        target_public_key_text=target_public_key_text,
    )


def resolve_identity_link_signature_path(record_path: Path) -> Path | None:
    candidate = record_path.with_name(f"{record_path.name}.asc")
    return candidate if candidate.exists() else None


def resolve_identity_link_public_key_path(record_path: Path) -> Path | None:
    candidate = record_path.with_name(f"{record_path.name}.pub.asc")
    return candidate if candidate.exists() else None


def parse_identity_link_record(path: Path) -> IdentityLinkRecord:
    record = parse_identity_link_text(path.read_text(encoding="ascii"), source_path=path)
    signature_path = resolve_identity_link_signature_path(path)
    public_key_path = resolve_identity_link_public_key_path(path)

    signer_fingerprint = None
    identity_id = None
    if public_key_path is not None:
        signer_fingerprint = fingerprint_from_public_key_path(public_key_path)
        identity_id = build_identity_id(signer_fingerprint)

    return IdentityLinkRecord(
        record_id=record.record_id,
        action=record.action,
        source_identity_id=record.source_identity_id,
        target_identity_id=record.target_identity_id,
        timestamp=record.timestamp,
        note=record.note,
        path=record.path,
        target_public_key_text=record.target_public_key_text,
        signature_path=signature_path,
        public_key_path=public_key_path,
        signer_fingerprint=signer_fingerprint,
        identity_id=identity_id,
    )


def load_identity_link_records(records_dir: Path) -> list[IdentityLinkRecord]:
    if not records_dir.exists():
        return []
    records = [parse_identity_link_record(path) for path in sorted(records_dir.glob("*.txt"))]
    return sorted(records, key=lambda record: (record.timestamp, record.record_id))


def collect_visible_identity_ids(*, identity_bootstrap_ids: list[str], post_identity_ids: list[str]) -> frozenset[str]:
    return frozenset(
        identity_id
        for identity_id in identity_bootstrap_ids + post_identity_ids
        if identity_id
    )


def derive_identity_resolution(
    *,
    visible_identity_ids: frozenset[str],
    link_records: list[IdentityLinkRecord],
) -> IdentityResolution:
    nodes = set(visible_identity_ids)
    for record in link_records:
        nodes.add(record.source_identity_id)
        nodes.add(record.target_identity_id)

    reciprocal_merge_pairs = {
        tuple(sorted((record.source_identity_id, record.target_identity_id)))
        for record in link_records
        if record.action == "merge_identity"
        and any(
            candidate.action == "merge_identity"
            and candidate.source_identity_id == record.target_identity_id
            and candidate.target_identity_id == record.source_identity_id
            for candidate in link_records
        )
    }

    adjacency: dict[str, set[str]] = {identity_id: set() for identity_id in nodes}
    for record in link_records:
        if record.action == "rotate_key":
            adjacency[record.source_identity_id].add(record.target_identity_id)
            adjacency[record.target_identity_id].add(record.source_identity_id)
            continue

        pair = tuple(sorted((record.source_identity_id, record.target_identity_id)))
        if pair in reciprocal_merge_pairs:
            adjacency[record.source_identity_id].add(record.target_identity_id)
            adjacency[record.target_identity_id].add(record.source_identity_id)

    canonical_by_identity_id: dict[str, str] = {}
    members_by_canonical_identity_id: dict[str, tuple[str, ...]] = {}
    seen: set[str] = set()

    for identity_id in sorted(adjacency):
        if identity_id in seen:
            continue

        stack = [identity_id]
        component: set[str] = set()
        while stack:
            current_identity_id = stack.pop()
            if current_identity_id in component:
                continue
            component.add(current_identity_id)
            stack.extend(sorted(adjacency[current_identity_id] - component))

        seen.update(component)
        if not component.intersection(visible_identity_ids):
            continue

        canonical_identity_id = min(component)
        members = tuple(sorted(component))
        members_by_canonical_identity_id[canonical_identity_id] = members
        for member_identity_id in members:
            canonical_by_identity_id[member_identity_id] = canonical_identity_id

    for identity_id in sorted(visible_identity_ids):
        if identity_id in canonical_by_identity_id:
            continue
        canonical_by_identity_id[identity_id] = identity_id
        members_by_canonical_identity_id[identity_id] = (identity_id,)

    return IdentityResolution(
        canonical_by_identity_id=canonical_by_identity_id,
        members_by_canonical_identity_id=members_by_canonical_identity_id,
    )
