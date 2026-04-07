from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Iterable

from forum_core.moderation import derive_moderation_state, load_moderation_records, moderation_records_dir, post_is_hidden, thread_is_hidden
from forum_core.moderation import parse_moderation_record
from forum_core.post_index import IndexedPostRow, load_indexed_root_posts
from forum_core.php_native_reads_db import connect_php_native_reads_db, delete_php_native_snapshot, php_native_reads_db_path, save_php_native_snapshot
from forum_core.thread_title_updates import parse_thread_title_update_record
from forum_core.thread_title_updates import load_thread_title_update_records, resolve_current_thread_title, thread_title_updates_dir
from forum_core.identity import identity_slug
from forum_web.repository import group_threads, index_posts, index_threads, load_posts, root_thread_type


def php_native_reads_dir(repo_root: Path) -> Path:
    return repo_root / "state" / "cache" / "php_native_reads"


def post_records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "posts"


def board_index_snapshot_path(repo_root: Path) -> Path:
    return php_native_reads_dir(repo_root) / "board_index_root.json"


def thread_snapshot_id(thread_id: str) -> str:
    return f"thread/{thread_id}"


def profile_snapshot_id(profile_slug: str) -> str:
    return f"profile/{profile_slug}"


def compose_reply_snapshot_id(thread_id: str, parent_id: str) -> str:
    return f"compose-reply/{thread_id}/{parent_id}"


def thread_snapshot_db_path(repo_root: Path) -> Path:
    return php_native_reads_db_path(repo_root)


def _first_line(text: str) -> str:
    for line in text.splitlines():
        trimmed = line.strip()
        if trimmed:
            return trimmed
    return ""


def _indexed_timestamp_value(timestamp_text: str | None) -> float:
    if not timestamp_text:
        return float("-inf")
    try:
        return datetime.fromisoformat(timestamp_text).timestamp()
    except ValueError:
        return float("-inf")


def _indexed_thread_sort_key(thread, moderation_state, *, indexed_roots: dict[str, IndexedPostRow]):
    indexed_root = indexed_roots.get(thread.root.post_id)
    updated_at = _indexed_timestamp_value(indexed_root.updated_at if indexed_root is not None else None)
    created_at = _indexed_timestamp_value(indexed_root.created_at if indexed_root is not None else None)
    return (
        0 if moderation_state.pins_thread(thread.root.post_id) else 1,
        -updated_at,
        -created_at,
        thread.root.post_id,
    )


def _visible_reply_count(thread, moderation_state) -> int:
    return sum(
        0
        if post_is_hidden(moderation_state, reply.post_id, thread.root.post_id)
        else 1
        for reply in thread.replies
    )


def _thread_timestamp_text(indexed_root: IndexedPostRow | None) -> str | None:
    if indexed_root is None:
        return None
    return indexed_root.updated_at or indexed_root.created_at


def build_board_index_snapshot(repo_root: Path) -> dict[str, object]:
    posts = load_posts(post_records_dir(repo_root))
    threads = group_threads(posts)
    moderation_state = derive_moderation_state(load_moderation_records(moderation_records_dir(repo_root)))
    indexed_roots = load_indexed_root_posts(repo_root)
    title_updates = load_thread_title_update_records(thread_title_updates_dir(repo_root))
    public_threads = sorted(
        [
            thread
            for thread in threads
            if not thread_is_hidden(moderation_state, thread.root.post_id)
        ],
        key=lambda thread: _indexed_thread_sort_key(
            thread,
            moderation_state,
            indexed_roots=indexed_roots,
        ),
    )
    board_tags = sorted({tag for thread in public_threads for tag in thread.root.board_tags})
    thread_rows: list[dict[str, object]] = []
    for thread in public_threads:
        subject = resolve_current_thread_title(
            thread_id=thread.root.post_id,
            root_subject=thread.root.subject or "Untitled thread",
            updates=title_updates,
        )
        preview = _first_line(thread.root.body) or "No preview available."
        visible_tags = tuple(tag for tag in thread.root.board_tags if tag and tag != "general")
        thread_rows.append(
            {
                "post_id": thread.root.post_id,
                "thread_href": f"/threads/{thread.root.post_id}",
                "subject": subject,
                "preview": preview,
                "tags": list(visible_tags),
                "reply_count": _visible_reply_count(thread, moderation_state),
                "thread_type": root_thread_type(thread.root),
                "last_activity_at": _thread_timestamp_text(indexed_roots.get(thread.root.post_id)),
            }
        )
    return {
        "route": "/",
        "thread_rows": thread_rows,
        "stats": {
            "post_count": len(posts),
            "thread_count": len(public_threads),
            "board_tag_count": len(board_tags),
        },
    }


def _build_thread_content_html(thread_id: str, repo_root: Path) -> tuple[str, str]:
    from forum_web.templates import _html_block, _join_html_blocks, load_template
    from forum_web.web import (
        load_repository_state,
        load_thread_title_updates,
        render_post_card,
        render_thread_root_context,
        resolved_thread_heading,
        thread_status_labels,
        visible_reply_count,
    )

    _posts, grouped_threads, _board_tags, _moderation_records, moderation_state, identity_context = load_repository_state()
    title_updates = load_thread_title_updates(repo_root)
    thread = index_threads(grouped_threads).get(thread_id)
    if thread is None or thread_is_hidden(moderation_state, thread_id):
        raise LookupError(f"unknown thread: {thread_id}")

    locked = moderation_state.locks_thread(thread_id)
    reply_link_html = (
        f'<p><a class="thread-chip" href="/compose/reply?thread_id={thread.root.post_id}&parent_id={thread.root.post_id}">compose a reply</a></p>'
        if not locked
        else '<p class="status-note">This thread is locked by moderation. New replies are disabled.</p>'
    )
    change_title_link_html = f'<p><a class="thread-chip" href="/threads/{thread.root.post_id}/title">change title</a></p>'
    thread_labels = thread_status_labels(thread_id, moderation_state)
    visible_replies = visible_reply_count(thread, moderation_state)
    thread_meta = ""
    if visible_replies > 0:
        thread_meta = f"{visible_replies} visible repl{'y' if visible_replies == 1 else 'ies'} in this thread."
    if root_thread_type(thread.root):
        thread_meta = (
            f"{root_thread_type(thread.root)} thread. {thread_meta}"
            if thread_meta
            else f"{root_thread_type(thread.root)} thread."
        )
    if thread_labels:
        thread_meta = (thread_meta + " " if thread_meta else "") + " ".join(thread_labels) + "."
    thread_meta_html = f'<p class="thread-meta">{thread_meta}</p>' if thread_meta else ""
    replies_section_html = ""
    if visible_replies > 0:
        replies_section_html = _join_html_blocks(
            _html_block(
                """
                <section class="panel page-section">
                  <div class="section-head page-lede"><h2>Replies</h2></div>
                  <div class="post-stack">
                """
            ),
            "\n".join(
                render_post_card(
                    reply,
                    root_thread_id=thread.root.post_id,
                    identity_context=identity_context,
                    hidden=post_is_hidden(moderation_state, reply.post_id, thread.root.post_id),
                    compact_thread_view=True,
                )
                for reply in thread.replies
            ),
            _html_block(
                """
                  </div>
                </section>
                """
            ),
        )
    current_title = resolved_thread_heading(thread, title_updates)
    content_html = load_template("thread.html").substitute(
        thread_heading=current_title,
        thread_meta_html=thread_meta_html,
        reply_link_html=reply_link_html,
        change_title_link_html=change_title_link_html,
        root_context_html=render_thread_root_context(thread),
        root_post_html=render_post_card(
            thread.root,
            root_thread_id=thread.root.post_id,
            identity_context=identity_context,
            compact_thread_view=True,
            show_subject=False,
        ),
        replies_section_html=replies_section_html,
    )
    return current_title, content_html


def build_thread_snapshot(thread_id: str, repo_root: Path) -> dict[str, object]:
    previous_repo_root = os.environ.get("FORUM_REPO_ROOT")
    os.environ["FORUM_REPO_ROOT"] = str(repo_root.resolve())
    try:
        title, content_html = _build_thread_content_html(thread_id, repo_root)
    finally:
        if previous_repo_root is None:
            os.environ.pop("FORUM_REPO_ROOT", None)
        else:
            os.environ["FORUM_REPO_ROOT"] = previous_repo_root
    return {
        "route": f"/threads/{thread_id}",
        "thread_id": thread_id,
        "title": title,
        "content_html": content_html,
        "feed_href": f"/threads/{thread_id}?format=rss",
    }


def build_profile_snapshot(identity_id: str, repo_root: Path) -> dict[str, object]:
    from forum_web.web import render_profile_page
    from forum_web.profiles import find_profile_summary, load_identity_context

    posts = load_posts(post_records_dir(repo_root))
    identity_context = load_identity_context(repo_root=repo_root, posts=posts)
    summary = find_profile_summary(
        repo_root=repo_root,
        posts=posts,
        identity_id=identity_id,
        identity_context=identity_context,
    )
    if summary is None:
        raise LookupError(f"unknown identity: {identity_id}")
    profile_slug = identity_slug(summary.identity_id)
    content_html = render_profile_page(
        summary=summary,
        posts=posts,
        identity_context=identity_context,
        route_path=f"/profiles/{profile_slug}",
        self_request=False,
    )
    return {
        "route": f"/profiles/{profile_slug}",
        "identity_id": summary.identity_id,
        "profile_slug": profile_slug,
        "title": summary.display_name,
        "content_html": content_html,
    }


def build_compose_reply_snapshot(thread_id: str, parent_id: str, repo_root: Path) -> dict[str, object]:
    from forum_web.profiles import load_identity_context
    from forum_web.web import describe_board_tags, render_compose_page, render_compose_reference

    posts = load_posts(post_records_dir(repo_root))
    posts_by_id = index_posts(posts)
    moderation_state = derive_moderation_state(load_moderation_records(moderation_records_dir(repo_root)))
    identity_context = load_identity_context(repo_root=repo_root, posts=posts)

    thread = posts_by_id.get(thread_id)
    if thread is None or not thread.is_root or thread_is_hidden(moderation_state, thread_id):
        raise LookupError(f"unknown thread: {thread_id}")
    if moderation_state.locks_thread(thread_id):
        raise LookupError(f"locked thread: {thread_id}")

    resolved_parent_id = parent_id or thread.post_id
    parent_post = posts_by_id.get(resolved_parent_id)
    if (
        parent_post is None
        or parent_post.root_thread_id != thread.post_id
        or post_is_hidden(moderation_state, resolved_parent_id, thread.post_id)
    ):
        raise LookupError(f"unknown post: {resolved_parent_id}")

    board_tags = " ".join(thread.board_tags)
    page_html = render_compose_page(
        command_name="create_reply",
        endpoint_path="/api/create_reply",
        compose_heading="Compose a signed reply",
        compose_text="Generate or import a local OpenPGP key, sign a canonical reply payload in the browser, and submit the signed reply directly into repository storage.",
        dry_run=False,
        board_tags=board_tags,
        context_text=f"This signed reply will go into thread {thread.post_id} in {describe_board_tags(board_tags)} under parent {resolved_parent_id}. Reply linkage is filled in automatically.",
        thread_id=thread_id,
        parent_id=resolved_parent_id,
        compose_path="/compose/reply",
        breadcrumb_label="compose reply",
        reply_target_html=render_compose_reference(
            parent_post,
            root_thread_id=thread.post_id,
            identity_context=identity_context,
            all_posts=posts,
        ),
    )
    return {
        "route": f"/compose/reply?thread_id={thread_id}&parent_id={resolved_parent_id}",
        "thread_id": thread_id,
        "parent_id": resolved_parent_id,
        "title": "Compose a signed reply",
        "page_html": page_html,
    }


def _all_thread_ids(repo_root: Path) -> list[str]:
    posts = load_posts(post_records_dir(repo_root))
    return sorted(post.post_id for post in posts if post.is_root)


def _all_profile_identity_ids(repo_root: Path) -> list[str]:
    from forum_web.profiles import find_profile_summary, load_identity_context

    posts = load_posts(post_records_dir(repo_root))
    identity_context = load_identity_context(repo_root=repo_root, posts=posts)
    candidate_identity_ids = {
        identity_id
        for identity_id in identity_context.bootstraps_by_identity_id.keys()
    }
    candidate_identity_ids.update(
        post.identity_id
        for post in posts
        if post.identity_id
    )
    resolved_identity_ids: set[str] = set()
    for candidate_identity_id in candidate_identity_ids:
        summary = find_profile_summary(
            repo_root=repo_root,
            posts=posts,
            identity_id=candidate_identity_id,
            identity_context=identity_context,
        )
        if summary is not None:
            resolved_identity_ids.add(summary.identity_id)
    return sorted(resolved_identity_ids)


def _all_compose_reply_targets_for_thread(repo_root: Path, thread_id: str) -> list[str]:
    posts_by_id = index_posts(load_posts(post_records_dir(repo_root)))
    moderation_state = derive_moderation_state(load_moderation_records(moderation_records_dir(repo_root)))
    thread = posts_by_id.get(thread_id)
    if thread is None or not thread.is_root or thread_is_hidden(moderation_state, thread_id) or moderation_state.locks_thread(thread_id):
        return []
    targets = [thread.post_id]
    for post in sorted(posts_by_id.values(), key=lambda candidate: candidate.post_id):
        if post.post_id == thread.post_id:
            continue
        if post.root_thread_id != thread_id:
            continue
        if post_is_hidden(moderation_state, post.post_id, thread_id):
            continue
        targets.append(post.post_id)
    return targets


def _root_thread_id_for_post(repo_root: Path, post_id: str) -> str | None:
    posts = index_posts(load_posts(post_records_dir(repo_root)))
    post = posts.get(post_id)
    return None if post is None else post.root_thread_id


def _threads_from_post_paths(repo_root: Path, touched_paths: Iterable[str]) -> set[str]:
    posts_by_id = index_posts(load_posts(post_records_dir(repo_root)))
    thread_ids: set[str] = set()
    for touched_path in touched_paths:
        path = Path(touched_path)
        if path.parts[:2] != ("records", "posts") or path.suffix != ".txt":
            continue
        post_id = path.stem
        post = posts_by_id.get(post_id)
        if post is not None:
            thread_ids.add(post.root_thread_id)
    return thread_ids


def _threads_from_moderation_paths(repo_root: Path, touched_paths: Iterable[str]) -> set[str]:
    thread_ids: set[str] = set()
    for touched_path in touched_paths:
        path = repo_root / touched_path
        relative_parts = Path(touched_path).parts
        if relative_parts[:2] != ("records", "moderation") or path.suffix != ".txt" or not path.exists():
            continue
        record = parse_moderation_record(path)
        if record.target_type == "thread":
            thread_ids.add(record.target_id)
            continue
        thread_id = _root_thread_id_for_post(repo_root, record.target_id)
        if thread_id is not None:
            thread_ids.add(thread_id)
    return thread_ids


def _threads_from_title_update_paths(repo_root: Path, touched_paths: Iterable[str]) -> set[str]:
    thread_ids: set[str] = set()
    for touched_path in touched_paths:
        path = repo_root / touched_path
        relative_parts = Path(touched_path).parts
        if relative_parts[:2] != ("records", "thread-title-updates") or path.suffix != ".txt" or not path.exists():
            continue
        record = parse_thread_title_update_record(path)
        thread_ids.add(record.thread_id)
    return thread_ids


def _requires_broad_identity_refresh(touched_paths: Iterable[str]) -> bool:
    watched_prefixes = {
        ("records", "profile-updates"),
        ("records", "identity-links"),
        ("records", "merge-requests"),
        ("records", "identity"),
    }
    for touched_path in touched_paths:
        path = Path(touched_path)
        if path.suffix != ".txt":
            continue
        if path.parts[:2] in watched_prefixes:
            return True
    return False


def affected_thread_ids_for_touched_paths(repo_root: Path, touched_paths: Iterable[str]) -> list[str]:
    normalized_paths = tuple(touched_paths)
    if _requires_broad_identity_refresh(normalized_paths):
        return _all_thread_ids(repo_root)
    affected = set()
    affected.update(_threads_from_post_paths(repo_root, normalized_paths))
    affected.update(_threads_from_moderation_paths(repo_root, normalized_paths))
    affected.update(_threads_from_title_update_paths(repo_root, normalized_paths))
    return sorted(affected)


def refresh_thread_snapshot(repo_root: Path, thread_id: str, *, invalidated_by_post_id: str | None = None) -> None:
    connection = connect_php_native_reads_db(repo_root)
    try:
        try:
            snapshot = build_thread_snapshot(thread_id, repo_root)
        except LookupError:
            delete_php_native_snapshot(connection, thread_snapshot_id(thread_id))
            return
        save_php_native_snapshot(
            connection,
            snapshot_id=thread_snapshot_id(thread_id),
            entity_type="thread",
            entity_id=thread_id,
            snapshot=snapshot,
            invalidated_by_post_id=invalidated_by_post_id,
        )
    finally:
        connection.close()


def refresh_profile_snapshot(repo_root: Path, identity_id: str) -> None:
    connection = connect_php_native_reads_db(repo_root)
    try:
        try:
            snapshot = build_profile_snapshot(identity_id, repo_root)
        except LookupError:
            delete_php_native_snapshot(connection, profile_snapshot_id(identity_slug(identity_id)))
            return
        save_php_native_snapshot(
            connection,
            snapshot_id=profile_snapshot_id(snapshot["profile_slug"]),
            entity_type="profile",
            entity_id=identity_id,
            snapshot=snapshot,
        )
    finally:
        connection.close()


def refresh_compose_reply_snapshot(repo_root: Path, thread_id: str, parent_id: str) -> None:
    connection = connect_php_native_reads_db(repo_root)
    try:
        try:
            snapshot = build_compose_reply_snapshot(thread_id, parent_id, repo_root)
        except LookupError:
            delete_php_native_snapshot(connection, compose_reply_snapshot_id(thread_id, parent_id))
            return
        save_php_native_snapshot(
            connection,
            snapshot_id=compose_reply_snapshot_id(thread_id, parent_id),
            entity_type="compose_reply",
            entity_id=f"{thread_id}:{parent_id}",
            snapshot=snapshot,
            invalidated_by_post_id=parent_id,
        )
    finally:
        connection.close()


def rebuild_php_native_thread_snapshots(repo_root: Path, *, thread_ids: Iterable[str] | None = None) -> list[str]:
    refreshed: list[str] = []
    target_thread_ids = sorted(set(thread_ids if thread_ids is not None else _all_thread_ids(repo_root)))
    for thread_id in target_thread_ids:
        refresh_thread_snapshot(repo_root, thread_id)
        refreshed.append(thread_id)
    return refreshed


def rebuild_php_native_profile_snapshots(repo_root: Path, *, identity_ids: Iterable[str] | None = None) -> list[str]:
    refreshed: list[str] = []
    target_identity_ids = sorted(set(identity_ids if identity_ids is not None else _all_profile_identity_ids(repo_root)))
    for identity_id in target_identity_ids:
        refresh_profile_snapshot(repo_root, identity_id)
        refreshed.append(identity_id)
    return refreshed


def rebuild_php_native_compose_reply_snapshots(repo_root: Path, *, thread_ids: Iterable[str] | None = None) -> list[str]:
    refreshed: list[str] = []
    target_thread_ids = sorted(set(thread_ids if thread_ids is not None else _all_thread_ids(repo_root)))
    for thread_id in target_thread_ids:
        for parent_id in _all_compose_reply_targets_for_thread(repo_root, thread_id):
            refresh_compose_reply_snapshot(repo_root, thread_id, parent_id)
            refreshed.append(compose_reply_snapshot_id(thread_id, parent_id))
    return refreshed


def refresh_php_native_read_artifacts(repo_root: Path, *, touched_paths: Iterable[str] = ()) -> None:
    snapshot_path = board_index_snapshot_path(repo_root)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(
        json.dumps(build_board_index_snapshot(repo_root), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    affected_thread_ids = affected_thread_ids_for_touched_paths(repo_root, touched_paths)
    for thread_id in affected_thread_ids:
        refresh_thread_snapshot(repo_root, thread_id)
    rebuild_php_native_compose_reply_snapshots(repo_root, thread_ids=affected_thread_ids)
    rebuild_php_native_profile_snapshots(repo_root)
