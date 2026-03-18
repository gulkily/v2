from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from forum_core.identity_links import IdentityLinkRecord, IdentityResolution, ensure_identity_id_text
from forum_core.profile_updates import (
    ProfileUpdateRecord,
    ResolvedDisplayName,
    profile_update_sort_key,
    resolve_current_display_name,
)


ALLOWED_MERGE_REQUEST_ACTIONS = (
    "request_merge",
    "approve_merge",
    "dismiss_merge",
    "moderator_approve_merge",
)


@dataclass(frozen=True)
class MergeRequestRecord:
    record_id: str
    action: str
    requester_identity_id: str
    target_identity_id: str
    actor_identity_id: str
    timestamp: str
    note: str
    path: Path
    signature_path: Path | None = None
    public_key_path: Path | None = None
    signer_fingerprint: str | None = None
    identity_id: str | None = None


@dataclass(frozen=True)
class MergeRequestState:
    requester_identity_id: str
    target_identity_id: str
    latest_request_record_id: str
    latest_request_timestamp: str
    latest_request_note: str
    latest_response_action: str | None
    latest_response_record_id: str | None
    latest_response_timestamp: str | None
    approved_by_target: bool
    approved_by_moderator: bool
    dismissed: bool
    active_merge: bool
    pending: bool


@dataclass(frozen=True)
class HistoricalUsernameMatch:
    candidate_identity_id: str
    candidate_display_name: str
    shared_display_names: tuple[str, ...]


@dataclass(frozen=True)
class MergeManagementSummary:
    identity_id: str
    historical_matches: tuple[HistoricalUsernameMatch, ...]
    outgoing_requests: tuple[MergeRequestState, ...]
    incoming_requests: tuple[MergeRequestState, ...]
    dismissed_requests: tuple[MergeRequestState, ...]
    approved_requests: tuple[MergeRequestState, ...]


def merge_request_sort_key(record: MergeRequestRecord) -> tuple[str, str]:
    return record.timestamp, record.record_id


def merge_request_records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "merge-requests"


def ensure_timestamp_text(timestamp_text: str) -> str:
    try:
        datetime.strptime(timestamp_text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("Timestamp must use UTC ISO-8601 form YYYY-MM-DDTHH:MM:SSZ") from exc
    return timestamp_text


def parse_merge_request_text(raw_text: str, *, source_path: Path | None = None) -> MergeRequestRecord:
    header_text, separator, body_text = raw_text.partition("\n\n")
    if not separator:
        raise ValueError("merge-request text is missing header/body separator")

    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        if ": " not in line:
            raise ValueError(f"invalid merge-request header line: {line!r}")
        key, value = line.split(": ", 1)
        headers[key] = value.strip()

    record_id = headers.get("Record-ID")
    action = (headers.get("Action") or "").strip().lower()
    requester_identity_id = headers.get("Requester-Identity-ID")
    target_identity_id = headers.get("Target-Identity-ID")
    actor_identity_id = headers.get("Actor-Identity-ID")
    timestamp = headers.get("Timestamp")
    if (
        not record_id
        or not action
        or not requester_identity_id
        or not target_identity_id
        or not actor_identity_id
        or not timestamp
    ):
        raise ValueError("merge-request text is missing required headers")
    if action not in ALLOWED_MERGE_REQUEST_ACTIONS:
        raise ValueError(f"unsupported merge-request action: {action}")

    normalized_requester_identity_id = ensure_identity_id_text(
        requester_identity_id,
        field_name="Requester-Identity-ID",
    )
    normalized_target_identity_id = ensure_identity_id_text(
        target_identity_id,
        field_name="Target-Identity-ID",
    )
    normalized_actor_identity_id = ensure_identity_id_text(
        actor_identity_id,
        field_name="Actor-Identity-ID",
    )
    if normalized_requester_identity_id == normalized_target_identity_id:
        raise ValueError("Requester-Identity-ID and Target-Identity-ID must differ")

    return MergeRequestRecord(
        record_id=record_id,
        action=action,
        requester_identity_id=normalized_requester_identity_id,
        target_identity_id=normalized_target_identity_id,
        actor_identity_id=normalized_actor_identity_id,
        timestamp=ensure_timestamp_text(timestamp),
        note=body_text.rstrip("\n"),
        path=source_path or Path("<request>"),
    )


def resolve_merge_request_signature_path(record_path: Path) -> Path | None:
    candidate = record_path.with_name(f"{record_path.name}.asc")
    return candidate if candidate.exists() else None


def resolve_merge_request_public_key_path(record_path: Path) -> Path | None:
    candidate = record_path.with_name(f"{record_path.name}.pub.asc")
    return candidate if candidate.exists() else None


def parse_merge_request_record(path: Path) -> MergeRequestRecord:
    from forum_core.identity import build_identity_id, fingerprint_from_public_key_path

    record = parse_merge_request_text(path.read_text(encoding="ascii"), source_path=path)
    signature_path = resolve_merge_request_signature_path(path)
    public_key_path = resolve_merge_request_public_key_path(path)

    signer_fingerprint = None
    identity_id = None
    if public_key_path is not None:
        signer_fingerprint = fingerprint_from_public_key_path(public_key_path)
        identity_id = build_identity_id(signer_fingerprint)

    return MergeRequestRecord(
        record_id=record.record_id,
        action=record.action,
        requester_identity_id=record.requester_identity_id,
        target_identity_id=record.target_identity_id,
        actor_identity_id=record.actor_identity_id,
        timestamp=record.timestamp,
        note=record.note,
        path=record.path,
        signature_path=signature_path,
        public_key_path=public_key_path,
        signer_fingerprint=signer_fingerprint,
        identity_id=identity_id,
    )


def load_merge_request_records(records_dir: Path) -> list[MergeRequestRecord]:
    if not records_dir.exists():
        return []
    records = [parse_merge_request_record(path) for path in sorted(records_dir.glob("*.txt"))]
    return sorted(records, key=merge_request_sort_key)


def derive_merge_request_states(records: list[MergeRequestRecord]) -> tuple[MergeRequestState, ...]:
    by_pair: dict[tuple[str, str], list[MergeRequestRecord]] = {}
    for record in sorted(records, key=merge_request_sort_key):
        pair = (record.requester_identity_id, record.target_identity_id)
        by_pair.setdefault(pair, []).append(record)

    states: list[MergeRequestState] = []
    for requester_identity_id, target_identity_id in sorted(by_pair):
        pair_records = by_pair[(requester_identity_id, target_identity_id)]
        latest_request = max(
            (record for record in pair_records if record.action == "request_merge"),
            key=merge_request_sort_key,
            default=None,
        )
        if latest_request is None:
            continue

        latest_target_response = max(
            (
                record
                for record in pair_records
                if record.action in {"approve_merge", "dismiss_merge"}
                and merge_request_sort_key(record) > merge_request_sort_key(latest_request)
            ),
            key=merge_request_sort_key,
            default=None,
        )
        latest_moderator_approval = max(
            (
                record
                for record in pair_records
                if record.action == "moderator_approve_merge"
                and merge_request_sort_key(record) > merge_request_sort_key(latest_request)
            ),
            key=merge_request_sort_key,
            default=None,
        )

        approved_by_target = latest_target_response is not None and latest_target_response.action == "approve_merge"
        dismissed = latest_target_response is not None and latest_target_response.action == "dismiss_merge"
        approved_by_moderator = latest_moderator_approval is not None
        active_merge = approved_by_target or approved_by_moderator
        pending = not dismissed and not active_merge

        latest_response = latest_target_response
        if latest_moderator_approval is not None and (
            latest_response is None
            or merge_request_sort_key(latest_moderator_approval) > merge_request_sort_key(latest_response)
        ):
            latest_response = latest_moderator_approval

        states.append(
            MergeRequestState(
                requester_identity_id=requester_identity_id,
                target_identity_id=target_identity_id,
                latest_request_record_id=latest_request.record_id,
                latest_request_timestamp=latest_request.timestamp,
                latest_request_note=latest_request.note,
                latest_response_action=latest_response.action if latest_response is not None else None,
                latest_response_record_id=latest_response.record_id if latest_response is not None else None,
                latest_response_timestamp=latest_response.timestamp if latest_response is not None else None,
                approved_by_target=approved_by_target,
                approved_by_moderator=approved_by_moderator,
                dismissed=dismissed,
                active_merge=active_merge,
                pending=pending,
            )
        )

    return tuple(states)


def derive_approved_merge_links(
    states: tuple[MergeRequestState, ...],
    *,
    resolution: IdentityResolution | None = None,
) -> tuple[IdentityLinkRecord, ...]:
    links: list[IdentityLinkRecord] = []
    for state in states:
        if not state.active_merge:
            continue
        pair_label = state.latest_response_record_id or state.latest_request_record_id
        requester_identity_ids = (
            resolution.member_identity_ids(state.requester_identity_id)
            if resolution is not None
            else ()
        ) or (state.requester_identity_id,)
        target_identity_ids = (
            resolution.member_identity_ids(state.target_identity_id)
            if resolution is not None
            else ()
        ) or (state.target_identity_id,)
        derived_pairs = sorted(
            {
                (source_identity_id, target_identity_id)
                for source_identity_id in requester_identity_ids
                for target_identity_id in target_identity_ids
                if source_identity_id != target_identity_id
            }
            | {
                (source_identity_id, target_identity_id)
                for source_identity_id in target_identity_ids
                for target_identity_id in requester_identity_ids
                if source_identity_id != target_identity_id
            }
        )
        for source_identity_id, target_identity_id in derived_pairs:
            links.append(
                IdentityLinkRecord(
                    record_id=f"derived-merge-{pair_label}-{source_identity_id.replace(':', '-')}",
                    action="merge_identity",
                    source_identity_id=source_identity_id,
                    target_identity_id=target_identity_id,
                    timestamp=state.latest_response_timestamp or state.latest_request_timestamp,
                    note="derived from approved merge request",
                    path=Path("<derived-merge-request>"),
                )
            )
    return tuple(sorted(links, key=lambda record: (record.timestamp, record.record_id)))


def display_name_history_by_canonical_identity_id(
    *,
    resolution: IdentityResolution,
    profile_updates: list[ProfileUpdateRecord],
) -> dict[str, tuple[str, ...]]:
    history: dict[str, list[tuple[tuple[str, str], str]]] = {}
    for record in sorted(profile_updates, key=profile_update_sort_key):
        canonical_identity_id = resolution.canonical_identity_id(record.source_identity_id)
        if canonical_identity_id is None:
            continue
        entries = history.setdefault(canonical_identity_id, [])
        if any(existing_display_name == record.display_name for _, existing_display_name in entries):
            continue
        entries.append((profile_update_sort_key(record), record.display_name))
    return {
        canonical_identity_id: tuple(display_name for _, display_name in entries)
        for canonical_identity_id, entries in history.items()
    }


def current_display_names_by_canonical_identity_id(
    *,
    resolution: IdentityResolution,
    profile_updates: list[ProfileUpdateRecord],
) -> dict[str, ResolvedDisplayName]:
    display_names: dict[str, ResolvedDisplayName] = {}
    for canonical_identity_id, member_identity_ids in resolution.members_by_canonical_identity_id.items():
        resolved = resolve_current_display_name(
            member_identity_ids=member_identity_ids,
            profile_updates=profile_updates,
        )
        if resolved is not None:
            display_names[canonical_identity_id] = resolved
    return display_names


def derive_historical_username_matches(
    *,
    identity_id: str,
    resolution: IdentityResolution,
    profile_updates: list[ProfileUpdateRecord],
) -> tuple[HistoricalUsernameMatch, ...]:
    canonical_identity_id = resolution.canonical_identity_id(identity_id)
    if canonical_identity_id is None:
        return ()

    history_by_canonical_identity_id = display_name_history_by_canonical_identity_id(
        resolution=resolution,
        profile_updates=profile_updates,
    )
    source_history = frozenset(history_by_canonical_identity_id.get(canonical_identity_id, ()))
    if not source_history:
        return ()

    current_display_names = current_display_names_by_canonical_identity_id(
        resolution=resolution,
        profile_updates=profile_updates,
    )

    matches: list[HistoricalUsernameMatch] = []
    for candidate_identity_id in sorted(resolution.members_by_canonical_identity_id):
        if candidate_identity_id == canonical_identity_id:
            continue
        candidate_history = frozenset(history_by_canonical_identity_id.get(candidate_identity_id, ()))
        shared_display_names = tuple(sorted(source_history.intersection(candidate_history)))
        if not shared_display_names:
            continue
        current_display_name = current_display_names.get(candidate_identity_id)
        matches.append(
            HistoricalUsernameMatch(
                candidate_identity_id=candidate_identity_id,
                candidate_display_name=(
                    current_display_name.display_name
                    if current_display_name is not None
                    else candidate_identity_id
                ),
                shared_display_names=shared_display_names,
            )
        )

    return tuple(matches)


def derive_merge_management_summary(
    *,
    identity_id: str,
    resolution: IdentityResolution,
    profile_updates: list[ProfileUpdateRecord],
    states: tuple[MergeRequestState, ...],
) -> MergeManagementSummary | None:
    canonical_identity_id = resolution.canonical_identity_id(identity_id)
    if canonical_identity_id is None:
        return None

    outgoing_requests: list[MergeRequestState] = []
    incoming_requests: list[MergeRequestState] = []
    dismissed_requests: list[MergeRequestState] = []
    approved_requests: list[MergeRequestState] = []

    for state in states:
        requester_canonical_identity_id = resolution.canonical_identity_id(state.requester_identity_id)
        target_canonical_identity_id = resolution.canonical_identity_id(state.target_identity_id)

        if state.active_merge and (
            requester_canonical_identity_id == canonical_identity_id
            or target_canonical_identity_id == canonical_identity_id
        ):
            approved_requests.append(state)
            continue
        if state.dismissed and target_canonical_identity_id == canonical_identity_id:
            dismissed_requests.append(state)
            continue
        if state.pending and requester_canonical_identity_id == canonical_identity_id:
            outgoing_requests.append(state)
            continue
        if state.pending and target_canonical_identity_id == canonical_identity_id:
            incoming_requests.append(state)

    return MergeManagementSummary(
        identity_id=canonical_identity_id,
        historical_matches=derive_historical_username_matches(
            identity_id=canonical_identity_id,
            resolution=resolution,
            profile_updates=profile_updates,
        ),
        outgoing_requests=tuple(
            sorted(outgoing_requests, key=lambda state: (state.latest_request_timestamp, state.latest_request_record_id))
        ),
        incoming_requests=tuple(
            sorted(incoming_requests, key=lambda state: (state.latest_request_timestamp, state.latest_request_record_id))
        ),
        dismissed_requests=tuple(
            sorted(dismissed_requests, key=lambda state: (state.latest_request_timestamp, state.latest_request_record_id))
        ),
        approved_requests=tuple(
            sorted(approved_requests, key=lambda state: (state.latest_request_timestamp, state.latest_request_record_id))
        ),
    )
