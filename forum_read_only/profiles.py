from __future__ import annotations

from pathlib import Path

from forum_core.identity import (
    IdentityBootstrap,
    ProfileSummary,
    index_identity_bootstraps,
    load_identity_bootstraps,
)
from forum_read_only.repository import Post


def identity_records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "identity"


def find_profile_summary(
    *,
    repo_root: Path,
    posts: list[Post],
    identity_id: str,
) -> ProfileSummary | None:
    explicit_bootstrap = index_identity_bootstraps(
        load_identity_bootstraps(identity_records_dir(repo_root)),
    ).get(identity_id)
    bootstrap = explicit_bootstrap or synthetic_bootstrap(posts, identity_id)
    if bootstrap is None:
        return None

    matching_posts = tuple(
        sorted(
            [post for post in posts if post.identity_id == identity_id],
            key=lambda post: post.post_id,
        )
    )
    thread_ids = tuple(sorted({post.root_thread_id for post in matching_posts}))
    return ProfileSummary(
        identity_id=bootstrap.identity_id,
        signer_fingerprint=bootstrap.signer_fingerprint,
        bootstrap_record_id=bootstrap.record_id,
        bootstrap_post_id=bootstrap.bootstrap_post_id,
        bootstrap_thread_id=bootstrap.bootstrap_thread_id,
        bootstrap_path=str(bootstrap.path.relative_to(repo_root)),
        post_ids=tuple(post.post_id for post in matching_posts),
        thread_ids=thread_ids,
        public_key_text=bootstrap.public_key_text,
    )


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
