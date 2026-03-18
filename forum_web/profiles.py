from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from forum_core.identity import (
    IdentityBootstrap,
    ProfileSummary,
    index_identity_bootstraps,
    load_identity_bootstraps,
    short_identity_label,
)
from forum_core.identity_links import (
    IdentityResolution,
    collect_visible_identity_ids,
    derive_identity_resolution,
    identity_link_records_dir,
    load_identity_link_records,
)
from forum_core.merge_requests import (
    MergeRequestRecord,
    MergeRequestState,
    derive_approved_merge_links,
    derive_merge_request_states,
    load_merge_request_records,
    merge_request_records_dir,
)
from forum_core.profile_updates import (
    ProfileUpdateRecord,
    ResolvedDisplayName,
    profile_update_sort_key,
    profile_update_records_dir,
    load_profile_update_records,
    resolve_current_display_name,
)
from forum_web.repository import Post


@dataclass(frozen=True)
class IdentityContext:
    bootstraps_by_identity_id: dict[str, IdentityBootstrap]
    resolution: IdentityResolution
    profile_update_records: tuple[ProfileUpdateRecord, ...]
    merge_request_records: tuple[MergeRequestRecord, ...]
    merge_request_states: tuple[MergeRequestState, ...]

    def canonical_identity_id(self, identity_id: str | None) -> str | None:
        return self.resolution.canonical_identity_id(identity_id)

    def member_identity_ids(self, identity_id: str | None) -> tuple[str, ...]:
        return self.resolution.member_identity_ids(identity_id)

    def resolved_display_name(self, identity_id: str | None) -> ResolvedDisplayName | None:
        member_identity_ids = self.member_identity_ids(identity_id)
        if not member_identity_ids:
            canonical_identity_id = self.canonical_identity_id(identity_id)
            if canonical_identity_id is None:
                return None
            member_identity_ids = (canonical_identity_id,)
        return resolve_current_display_name(
            member_identity_ids=member_identity_ids,
            profile_updates=list(self.profile_update_records),
        )


def identity_records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "identity"


def load_identity_context(*, repo_root: Path, posts: list[Post]) -> IdentityContext:
    bootstraps = load_identity_bootstraps(identity_records_dir(repo_root))
    merge_request_records = tuple(load_merge_request_records(merge_request_records_dir(repo_root)))
    merge_request_states = derive_merge_request_states(list(merge_request_records))
    link_records = load_identity_link_records(identity_link_records_dir(repo_root))
    resolution = derive_identity_resolution(
        visible_identity_ids=collect_visible_identity_ids(
            identity_bootstrap_ids=[bootstrap.identity_id for bootstrap in bootstraps],
            post_identity_ids=[post.identity_id or "" for post in posts],
        ),
        link_records=link_records + list(derive_approved_merge_links(merge_request_states)),
    )
    return IdentityContext(
        bootstraps_by_identity_id=index_identity_bootstraps(bootstraps),
        resolution=resolution,
        profile_update_records=tuple(
            load_profile_update_records(profile_update_records_dir(repo_root))
        ),
        merge_request_records=merge_request_records,
        merge_request_states=merge_request_states,
    )


def find_profile_summary(
    *,
    repo_root: Path,
    posts: list[Post],
    identity_id: str,
    identity_context: IdentityContext | None = None,
) -> ProfileSummary | None:
    context = identity_context or load_identity_context(repo_root=repo_root, posts=posts)
    canonical_identity_id = context.canonical_identity_id(identity_id)
    if canonical_identity_id is None:
        return None

    member_identity_ids = context.member_identity_ids(canonical_identity_id) or (canonical_identity_id,)
    bootstrap = select_profile_bootstrap(
        posts=posts,
        bootstraps_by_identity_id=context.bootstraps_by_identity_id,
        member_identity_ids=member_identity_ids,
    )
    if bootstrap is None:
        return None

    fallback_display_name = short_identity_label(bootstrap.signer_fingerprint)
    resolved_display_name = resolve_current_display_name(
        member_identity_ids=member_identity_ids,
        profile_updates=list(context.profile_update_records),
    )
    matching_posts = tuple(
        sorted(
            [post for post in posts if post.identity_id in member_identity_ids],
            key=lambda post: post.post_id,
        )
    )
    thread_ids = tuple(sorted({post.root_thread_id for post in matching_posts}))
    return ProfileSummary(
        identity_id=canonical_identity_id,
        bootstrap_identity_id=bootstrap.identity_id,
        signer_fingerprint=bootstrap.signer_fingerprint,
        display_name=(
            resolved_display_name.display_name
            if resolved_display_name is not None
            else fallback_display_name
        ),
        display_name_source=(
            "profile_update"
            if resolved_display_name is not None
            else "fingerprint_fallback"
        ),
        fallback_display_name=fallback_display_name,
        bootstrap_record_id=bootstrap.record_id,
        bootstrap_post_id=bootstrap.bootstrap_post_id,
        bootstrap_thread_id=bootstrap.bootstrap_thread_id,
        bootstrap_path=str(bootstrap.path.relative_to(repo_root)),
        member_identity_ids=member_identity_ids,
        post_ids=tuple(post.post_id for post in matching_posts),
        thread_ids=thread_ids,
        public_key_text=bootstrap.public_key_text,
        display_name_record_id=(
            resolved_display_name.record_id
            if resolved_display_name is not None
            else None
        ),
        display_name_source_identity_id=(
            resolved_display_name.source_identity_id
            if resolved_display_name is not None
            else None
        ),
    )


def select_profile_bootstrap(
    *,
    posts: list[Post],
    bootstraps_by_identity_id: dict[str, IdentityBootstrap],
    member_identity_ids: tuple[str, ...],
) -> IdentityBootstrap | None:
    for identity_id in member_identity_ids:
        explicit_bootstrap = bootstraps_by_identity_id.get(identity_id)
        if explicit_bootstrap is not None:
            return explicit_bootstrap
    for identity_id in member_identity_ids:
        synthetic = synthetic_bootstrap(posts, identity_id)
        if synthetic is not None:
            return synthetic
    return None


def synthetic_bootstrap(posts: list[Post], identity_id: str) -> IdentityBootstrap | None:
    candidates = sorted(
        [
            post
            for post in posts
            if post.identity_id == identity_id
            and post.public_key_path is not None
            and post.signer_fingerprint is not None
        ],
        key=lambda post: post.post_id,
    )
    if not candidates:
        return None

    post = candidates[0]
    return IdentityBootstrap(
        record_id=post.post_id,
        identity_id=identity_id,
        signer_fingerprint=post.signer_fingerprint or "",
        bootstrap_post_id=post.post_id,
        bootstrap_thread_id=post.root_thread_id,
        public_key_text=post.public_key_path.read_text(encoding="ascii"),
        path=post.public_key_path or post.path,
    )


def resolve_identity_display_name(
    *,
    identity_context: IdentityContext,
    identity_id: str | None,
    fallback_display_name: str,
) -> str:
    resolved_display_name = identity_context.resolved_display_name(identity_id)
    if resolved_display_name is None:
        return fallback_display_name
    return resolved_display_name.display_name


def username_route_token(display_name: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", display_name.strip().lower()).strip("-")
    return token


def profile_usernames(
    *,
    identity_context: IdentityContext,
    identity_id: str,
) -> tuple[str, ...]:
    canonical_identity_id = identity_context.canonical_identity_id(identity_id)
    if canonical_identity_id is None:
        return ()
    member_identity_ids = identity_context.member_identity_ids(canonical_identity_id) or (canonical_identity_id,)
    member_identity_id_set = frozenset(member_identity_ids)
    usernames: list[str] = []
    current_display_name = resolve_current_display_name(
        member_identity_ids=member_identity_ids,
        profile_updates=list(identity_context.profile_update_records),
    )
    if current_display_name is not None:
        usernames.append(current_display_name.display_name)
    for record in sorted(identity_context.profile_update_records, key=profile_update_sort_key, reverse=True):
        if record.source_identity_id not in member_identity_id_set:
            continue
        if record.display_name in usernames:
            continue
        usernames.append(record.display_name)
    return tuple(usernames)


def resolve_profile_summary_by_username(
    *,
    repo_root: Path,
    posts: list[Post],
    username: str,
    identity_context: IdentityContext | None = None,
) -> ProfileSummary | None:
    context = identity_context or load_identity_context(repo_root=repo_root, posts=posts)
    requested_token = username_route_token(username)
    if not requested_token:
        return None

    matching_identity_ids: list[str] = []
    for canonical_identity_id, member_identity_ids in context.resolution.members_by_canonical_identity_id.items():
        resolved_display_name = resolve_current_display_name(
            member_identity_ids=member_identity_ids,
            profile_updates=list(context.profile_update_records),
        )
        if resolved_display_name is None:
            continue
        if username_route_token(resolved_display_name.display_name) != requested_token:
            continue
        matching_identity_ids.append(canonical_identity_id)

    if len(matching_identity_ids) != 1:
        return None

    return find_profile_summary(
        repo_root=repo_root,
        posts=posts,
        identity_id=matching_identity_ids[0],
        identity_context=context,
    )
