from __future__ import annotations

import html
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from urllib.parse import parse_qs, unquote
from wsgiref.util import setup_testing_defaults

from forum_core.instance_info import load_instance_info, render_public_value
from forum_core.identity import identity_id_from_slug, identity_slug, short_identity_label
from forum_core.llm_provider import LLMProviderError, get_llm_model, run_llm
from forum_core.post_index import IndexedPostRow, load_indexed_root_posts
from forum_core.proof_of_work import first_post_pow_difficulty, first_post_pow_enabled
from forum_core.proof_of_work import pow_requirement_for_public_key
from forum_core.runtime_env import load_repo_env, notify_missing_env_defaults
from forum_core.moderation import (
    derive_moderation_state,
    load_moderation_records,
    moderation_log_slice,
    moderation_records_dir,
    post_is_hidden,
    thread_is_hidden,
)
from forum_cgi.identity_links import submit_identity_link
from forum_cgi.moderation import submit_moderation
from forum_cgi.posting import PostingError
from forum_cgi.profile_updates import submit_profile_update
from forum_cgi.service import submit_create_reply, submit_create_thread
from forum_cgi.task_status import TaskStatusUpdateResult, submit_mark_task_done
from forum_cgi.text import (
    render_error_body,
    render_identity_link_result,
    render_moderation_result,
    render_profile_update_result,
    render_submission_result,
)
from forum_web.api_text import (
    render_api_home_text,
    render_llms_text,
    render_bad_request_text,
    render_index_text,
    render_llm_result_text,
    render_moderation_log_text,
    render_not_found_text,
    render_post_text,
    render_profile_text,
    render_thread_text,
)
from forum_web.profiles import find_profile_summary, load_identity_context, resolve_identity_display_name
from forum_web.repository import (
    Post,
    group_threads,
    index_posts,
    index_threads,
    is_task_root,
    list_board_tags,
    load_posts,
    root_thread_type,
)
from forum_web.task_threads import index_task_threads, load_task_threads
from forum_web.templates import (
    load_asset_text,
    load_template,
    render_page,
    render_site_header,
)

load_repo_env()
notify_missing_env_defaults()


def get_repo_root() -> Path:
    env_root = os.environ.get("FORUM_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parent.parent


def load_repository_state():
    repo_root = get_repo_root()
    posts = load_posts(repo_root / "records" / "posts")
    threads = group_threads(posts)
    board_tags = list_board_tags(posts)
    moderation_records = load_moderation_records(moderation_records_dir(repo_root))
    moderation_state = derive_moderation_state(moderation_records)
    identity_context = load_identity_context(repo_root=repo_root, posts=posts)
    return posts, threads, board_tags, moderation_records, moderation_state, identity_context


@dataclass(frozen=True)
class GitCommitEntry:
    commit_id: str
    commit_date: str
    subject: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class ActivityEvent:
    kind: str
    sort_timestamp: datetime
    commit: GitCommitEntry | None = None
    moderation_record: object | None = None


def activity_filter_mode_from_request(raw_mode: str | None) -> str:
    mode = (raw_mode or "").strip().lower()
    if mode in {"content", "moderation", "code"}:
        return mode
    return "all"


def parse_activity_sort_timestamp(raw_value: str) -> datetime:
    normalized = raw_value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    return datetime.fromisoformat(normalized)


def fetch_recent_repository_commits(repo_root: Path, *, limit: int = 12) -> list[GitCommitEntry]:
    if limit <= 0:
        return []
    field_sep = "\x1f"
    format_string = f"%H{field_sep}%cI{field_sep}%s"
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "log",
            f"--max-count={limit}",
            f"--pretty=format:{format_string}",
            "--name-only",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return []
    entries: list[GitCommitEntry] = []
    current_base: tuple[str, str, str] | None = None
    current_files: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        if field_sep in line:
            if current_base is not None:
                entries.append(
                    GitCommitEntry(
                        commit_id=current_base[0],
                        commit_date=current_base[1],
                        subject=current_base[2],
                        files=tuple(current_files),
                    )
                )
            parts = line.split(field_sep, 2)
            if len(parts) != 3:
                current_base = None
                current_files = []
                continue
            current_base = (parts[0], parts[1], parts[2])
            current_files = []
        elif current_base is not None:
            normalized = line.strip()
            if normalized:
                current_files.append(normalized)
    if current_base is not None:
        entries.append(
            GitCommitEntry(
                commit_id=current_base[0],
                commit_date=current_base[1],
                subject=current_base[2],
                files=tuple(current_files),
            )
        )
    return entries


def fetch_recent_commits(repo_root: Path, *, limit: int = 12) -> list[GitCommitEntry]:
    return [
        commit
        for commit in fetch_recent_repository_commits(repo_root, limit=limit)
        if classify_commit_activity(commit) == "content"
    ][:limit]


def classify_commit_activity(commit: GitCommitEntry) -> str:
    normalized_files = tuple(Path(file_path).as_posix() for file_path in commit.files)
    if any(
        not path.startswith("records/posts/") and not path.startswith("records/moderation/")
        for path in normalized_files
    ):
        return "code"
    if any(path.startswith("records/moderation/") for path in normalized_files):
        return "moderation"
    return "content"


def build_posts_index(posts: list[Post], repo_root: Path) -> dict[str, Post]:
    index: dict[str, object] = {}
    for post in posts:
        try:
            relative = str(post.path.relative_to(repo_root))
        except ValueError:
            relative = str(post.path)
        index[relative] = post
    return index


def resolve_commit_posts(commit: GitCommitEntry, posts_index: dict[str, Post]) -> list[Post]:
    touched = []
    for file_path in commit.files:
        normalized = Path(file_path).as_posix()
        if normalized in posts_index:
            touched.append(posts_index[normalized])
    return touched


def load_activity_events(repo_root: Path, *, mode: str, limit: int = 12) -> list[ActivityEvent]:
    events: list[ActivityEvent] = []
    if mode in {"all", "content", "code"}:
        events.extend(
            ActivityEvent(
                kind=classify_commit_activity(commit),
                sort_timestamp=parse_activity_sort_timestamp(commit.commit_date),
                commit=commit,
            )
            for commit in fetch_recent_repository_commits(repo_root, limit=limit)
            if mode == "all" or classify_commit_activity(commit) == mode
        )
    if mode in {"all", "moderation"}:
        moderation_records = load_moderation_records(moderation_records_dir(repo_root))
        records = moderation_log_slice(moderation_records, limit=limit)
        events.extend(
            ActivityEvent(
                kind="moderation",
                sort_timestamp=parse_activity_sort_timestamp(record.timestamp),
                moderation_record=record,
            )
            for record in records
        )
    return sort_activity_events(events, limit=limit)


def sort_activity_events(events: list[ActivityEvent], *, limit: int = 12) -> list[ActivityEvent]:
    ordered = sorted(events, key=lambda event: event.sort_timestamp, reverse=True)
    return ordered[:limit]


def indexed_timestamp_value(timestamp_text: str | None) -> float:
    if not timestamp_text:
        return float("-inf")
    try:
        return datetime.fromisoformat(timestamp_text).timestamp()
    except ValueError:
        return float("-inf")


def indexed_thread_sort_key(thread, moderation_state, *, indexed_roots: dict[str, IndexedPostRow]):
    indexed_root = indexed_roots.get(thread.root.post_id)
    updated_at = indexed_timestamp_value(indexed_root.updated_at if indexed_root is not None else None)
    created_at = indexed_timestamp_value(indexed_root.created_at if indexed_root is not None else None)
    return (
        0 if moderation_state.pins_thread(thread.root.post_id) else 1,
        -updated_at,
        -created_at,
        thread.root.post_id,
    )


def visible_threads(threads, moderation_state, *, board_tag: str | None = None, repo_root: Path | None = None):
    filtered = [
        thread
        for thread in threads
        if not thread_is_hidden(moderation_state, thread.root.post_id)
    ]
    if board_tag:
        filtered = [thread for thread in filtered if board_tag in thread.root.board_tags]
    indexed_roots: dict[str, IndexedPostRow] = {}
    if repo_root is not None:
        try:
            indexed_roots = load_indexed_root_posts(repo_root, board_tag=board_tag)
        except Exception:
            indexed_roots = {}
    return sorted(
        filtered,
        key=lambda thread: indexed_thread_sort_key(
            thread,
            moderation_state,
            indexed_roots=indexed_roots,
        ),
    )


def visible_reply_count(thread, moderation_state) -> int:
    return sum(
        0
        if post_is_hidden(moderation_state, reply.post_id, thread.root.post_id)
        else 1
        for reply in thread.replies
    )


def thread_status_labels(thread_id: str, moderation_state) -> list[str]:
    labels = []
    if moderation_state.pins_thread(thread_id):
        labels.append("pinned")
    if moderation_state.locks_thread(thread_id):
        labels.append("locked")
    return labels


def parse_limit_value(raw_value: str | None, *, default: int = 20) -> int:
    if raw_value is None or not raw_value.strip():
        return default
    try:
        limit = int(raw_value)
    except ValueError as exc:
        raise PostingError("bad_request", "limit must be a decimal integer") from exc
    if limit < 1 or limit > 100:
        raise PostingError("bad_request", "limit must be between 1 and 100")
    return limit


def render_thread_status_badges(thread_id: str, moderation_state, *, thread_type: str | None = None) -> str:
    badges = []
    if thread_type:
        badges.append(thread_type)
    badges.extend("locked" if label == "locked" else "pinned" for label in thread_status_labels(thread_id, moderation_state))
    return "".join(f'<span class="thread-badge">{html.escape(label)}</span>' for label in badges)


def resolved_profile_identity_id(identity_context, identity_id: str | None) -> str | None:
    if identity_id is None:
        return None
    return identity_context.canonical_identity_id(identity_id) or identity_id


def render_board_index() -> str:
    repo_root = get_repo_root()
    posts, threads, _, _, moderation_state, _ = load_repository_state()
    context = build_board_index_page_context(posts, threads, moderation_state, repo_root=repo_root)
    content = load_template("board_index.html").substitute(context)
    return render_page(
        title="Forum Reader",
        hero_kicker="Board Index",
        hero_title="Threads gathered straight from canonical text records",
        hero_text="This board view reads the git-tracked post files directly, groups thread roots by board tags, and keeps the dataset browsable without adding a database or durable index layer.",
        content_html=content,
    )


def build_board_index_page_context(posts, threads, moderation_state, *, repo_root: Path) -> dict[str, str]:
    public_threads = visible_threads(threads, moderation_state, repo_root=repo_root)
    board_tags = sorted({tag for thread in public_threads for tag in thread.root.board_tags})
    return {
        "stats_html": render_board_index_stats(len(posts), len(public_threads), len(board_tags)),
        "thread_rows_html": render_board_index_thread_rows(public_threads, moderation_state),
        "action_links_html": render_board_index_action_links(),
    }


def render_board_index_stats(post_count: int, thread_count: int, board_tag_count: int) -> str:
    return (
        '<div class="stat-grid">'
        f'<article class="stat-card"><span class="stat-number">{post_count}</span><span class="stat-label">posts loaded</span></article>'
        f'<article class="stat-card"><span class="stat-number">{thread_count}</span><span class="stat-label">visible threads</span></article>'
        f'<article class="stat-card"><span class="stat-number">{board_tag_count}</span><span class="stat-label">board tags</span></article>'
        "</div>"
    )


def render_board_index_thread_rows(threads, moderation_state) -> str:
    return "".join(render_board_index_thread_row(index, thread, moderation_state) for index, thread in enumerate(threads, start=1))


def render_board_index_thread_row(rank: int, thread, moderation_state) -> str:
    subject = thread.root.subject or "Untitled thread"
    preview = first_line(thread.root.body) or "No preview available."
    tags_html = " ".join(f'[{html.escape(tag)}]' for tag in thread.root.board_tags)
    meta_parts = [
        f"{visible_reply_count(thread, moderation_state)} repl{'y' if visible_reply_count(thread, moderation_state) == 1 else 'ies'}",
        html.escape(thread.root.post_id),
    ]
    if root_thread_type(thread.root):
        meta_parts.append(html.escape(root_thread_type(thread.root)))
    meta_text = " · ".join(meta_parts)
    return (
        '<article class="board-index-thread-row">'
        f'<p class="board-index-thread-rank">{rank}.</p>'
        '<div class="board-index-thread-main">'
        f'<h3><a href="/threads/{html.escape(thread.root.post_id)}">{html.escape(subject)}</a></h3>'
        f'<p class="board-index-thread-tags">{tags_html}</p>'
        f'<p>{html.escape(preview)}</p>'
        f'<p class="thread-meta">{meta_text}</p>'
        "</div>"
        "</article>"
    )


def render_board_index_action_links() -> str:
    links = [
        ("/compose/thread", "compose a signed thread"),
        ("/instance/", "instance info"),
        ("/activity/", "view repository history"),
        ("/activity/?view=moderation", "moderation activity"),
        ("/planning/task-priorities/", "task priorities"),
    ]
    return "".join(
        f'<a class="thread-chip" href="{html.escape(path)}">{html.escape(label)}</a>'
        for path, label in links
    )


def load_recent_records(*, limit: int = 12):
    posts, _, _, _, _, identity_context = load_repository_state()
    if limit <= 0:
        return [], identity_context
    recent = posts[-limit:]
    return list(reversed(recent)), identity_context


def describe_git_worktree(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "-sb"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return "git status unavailable"
    status = result.stdout.strip()
    return status or "clean"


def git_status_summary(repo_root: Path) -> dict[str, str]:
    info = load_instance_info(repo_root)
    worktree_status = describe_git_worktree(repo_root)
    return {
        "commit_id": info.commit_id or "unknown",
        "commit_date": info.commit_date or "unknown",
        "source_path": str(info.source_path),
        "worktree": worktree_status,
        "git_worktree": worktree_status,
    }


def format_commit_date(commit_date: str) -> str:
    if not commit_date:
        return "unknown date"
    try:
        timestamp = datetime.fromisoformat(commit_date)
    except ValueError:
        return commit_date
    return timestamp.strftime("%b %d, %Y · %H:%M:%S %z")


def render_commit_card(
    commit: GitCommitEntry,
    posts: list[Post],
    identity_context,
    *,
    activity_kind: str = "content",
) -> str:
    post_cards = "".join(
        render_post_card(
            post,
            root_thread_id=post.root_thread_id,
            identity_context=identity_context,
            compact_thread_view=True,
        )
        for post in posts
    )
    if not post_cards:
        if activity_kind == "code":
            post_cards = '<p class="post-link">This code commit did not touch canonical post records.</p>'
        else:
            post_cards = '<p class="post-link">No canonical records were touched by this commit.</p>'
    activity_label = "Content commit"
    if activity_kind == "code":
        activity_label = "Code commit"
    return (
        '<article class="commit-card">'
        '<div class="commit-card-meta">'
        f'<p class="post-link">{html.escape(activity_label)}</p>'
        f'<p class="commit-id">Commit {html.escape(commit.commit_id[:12])}</p>'
        f'<p class="commit-date">{html.escape(format_commit_date(commit.commit_date))}</p>'
        f'<p class="commit-subject">{html.escape(commit.subject or "No message")}</p>'
        "</div>"
        '<div class="commit-posts">'
        f"{post_cards}"
        "</div>"
        "</article>"
    )


def render_activity_filter_nav(*, current_mode: str) -> str:
    links = [
        ("all", "/activity/", "all activity"),
        ("content", "/activity/?view=content", "content activity"),
        ("moderation", "/activity/?view=moderation", "moderation activity"),
        ("code", "/activity/?view=code", "code activity"),
    ]
    parts = []
    for mode, href, label in links:
        classes = "thread-chip"
        if mode == current_mode:
            classes += " thread-chip-active"
        parts.append(f'<a class="{classes}" href="{href}">{html.escape(label)}</a>')
    return "".join(parts)


def render_activity_event_card(event: ActivityEvent, *, posts_index: dict[str, Post], identity_context) -> str:
    if event.kind == "moderation" and event.moderation_record is not None:
        return render_moderation_card(event.moderation_record, identity_context=identity_context)
    assert event.commit is not None
    return render_commit_card(
        event.commit,
        resolve_commit_posts(event.commit, posts_index),
        identity_context,
        activity_kind=event.kind,
    )


def render_site_activity_page(*, view_mode: str) -> str:
    repo_root = get_repo_root()
    posts, _, _, _, _, identity_context = load_repository_state()
    posts_index = build_posts_index(posts, repo_root)
    events = load_activity_events(repo_root, mode=view_mode)
    event_cards = "".join(
        render_activity_event_card(
            event,
            posts_index=posts_index,
            identity_context=identity_context,
        )
        for event in events
    )
    if not event_cards:
        event_cards = '<article class="post-card"><p class="post-link">No activity matches this filter yet.</p></article>'
    git_summary = git_status_summary(repo_root)
    git_worktree_value = git_summary.get("git_worktree") or git_summary.get("worktree") or "git status unavailable"
    intro_text = "Browse one combined reverse-chronological timeline of content, moderation, and code changes."
    if view_mode == "content":
        intro_text = "Browse only git-backed content activity for this instance."
    elif view_mode == "moderation":
        intro_text = "Browse only signed moderation actions for this instance."
    elif view_mode == "code":
        intro_text = "Browse only repository code changes for this instance."
    content = load_template("activity.html").substitute(
        filter_nav_html=render_activity_filter_nav(current_mode=view_mode),
        activity_intro_text=html.escape(intro_text),
        event_cards_html=event_cards,
        git_commit_id=html.escape(git_summary.get("commit_id") or "unknown"),
        git_commit_date=html.escape(git_summary.get("commit_date") or "unknown"),
        git_source_path=html.escape(git_summary.get("source_path") or "unknown"),
        git_worktree=html.escape(git_worktree_value),
    )
    return render_page(
        title="Repository History",
        hero_kicker="Activity feed",
        hero_title="Repository history",
        hero_text="One filtered timeline for repository content, moderation, and code activity on this instance.",
        content_html=content,
    )


def render_board_section(tag: str, threads, moderation_state) -> str:
    thread_cards = "".join(
        "<article class=\"thread-card\">"
        f"{render_thread_status_badges(thread.root.post_id, moderation_state, thread_type=root_thread_type(thread.root))}"
        f"<p class=\"thread-id\">{html.escape(thread.root.post_id)}</p>"
        f"<h3><a href=\"/threads/{html.escape(thread.root.post_id)}\">{html.escape(thread.root.subject or 'Untitled thread')}</a></h3>"
        f"<p>{html.escape(first_line(thread.root.body))}</p>"
        f"<p class=\"thread-meta\">{visible_reply_count(thread, moderation_state)} repl{'y' if visible_reply_count(thread, moderation_state) == 1 else 'ies'}</p>"
        "</article>"
        for thread in threads
    )
    return (
        f'<section class="panel board-section" id="board-{html.escape(tag)}">'
        f'<div class="section-head"><h2>/{html.escape(tag)}/</h2>'
        f'<p>{len(threads)} thread{"s" if len(threads) != 1 else ""} in this board tag.</p></div>'
        f'<div class="thread-grid">{thread_cards}</div>'
        "</section>"
    )


def render_thread(thread_id: str) -> str:
    posts, grouped_threads, _, _, moderation_state, identity_context = load_repository_state()
    threads = index_threads(grouped_threads)
    thread = threads.get(thread_id)
    if thread is None or thread_is_hidden(moderation_state, thread_id):
        raise LookupError(f"unknown thread: {thread_id}")

    locked = moderation_state.locks_thread(thread_id)
    reply_link_html = (
        f'<p><a class="thread-chip" href="/compose/reply?thread_id={html.escape(thread.root.post_id)}&parent_id={html.escape(thread.root.post_id)}">compose a signed reply</a></p>'
        if not locked
        else '<p class="status-note">This thread is locked by moderation. New replies are disabled.</p>'
    )
    thread_labels = thread_status_labels(thread_id, moderation_state)
    thread_meta = f"{visible_reply_count(thread, moderation_state)} visible repl{'y' if visible_reply_count(thread, moderation_state) == 1 else 'ies'} in this thread."
    if root_thread_type(thread.root):
        thread_meta = f"{root_thread_type(thread.root)} thread. {thread_meta}"
    if thread_labels:
        thread_meta += " " + " ".join(thread_labels) + "."

    content = load_template("thread.html").substitute(
        breadcrumb_html=render_breadcrumb(
            [
                ('/', 'board index'),
                ('/threads/' + thread.root.post_id, 'thread'),
            ]
        ),
        thread_heading=html.escape(thread.root.subject or thread.root.post_id),
        thread_meta=thread_meta,
        reply_link_html=reply_link_html,
        root_context_html=render_thread_root_context(thread),
        root_post_html=render_post_card(
            thread.root,
            root_thread_id=thread.root.post_id,
            identity_context=identity_context,
            compact_thread_view=True,
            show_subject=False,
        ),
        replies_html="".join(
            render_post_card(
                reply,
                root_thread_id=thread.root.post_id,
                identity_context=identity_context,
                hidden=post_is_hidden(moderation_state, reply.post_id, thread.root.post_id),
                compact_thread_view=True,
            )
            for reply in thread.replies
        ),
    )
    return render_page(
        title=thread.root.subject or thread.root.post_id,
        hero_kicker="Thread View",
        hero_title=thread.root.subject or thread.root.post_id,
        hero_text=(
            "Task threads are typed root posts: the root carries structured task metadata, and replies stay ordinary task comments."
            if is_task_root(thread.root)
            else "The thread page is rendered directly from canonical post files without a database, using deterministic reply ordering from the repository state."
        ),
        content_html=content,
    )


def render_post(post_id: str) -> str:
    posts, _, _, _, moderation_state, identity_context = load_repository_state()
    post = index_posts(posts).get(post_id)
    if post is None:
        raise LookupError(f"unknown post: {post_id}")
    if thread_is_hidden(moderation_state, post.root_thread_id):
        raise LookupError(f"unknown post: {post_id}")

    thread_target = post.root_thread_id
    heading = post.subject or post.post_id
    hidden = post_is_hidden(moderation_state, post.post_id, thread_target)
    locked = moderation_state.locks_thread(thread_target)
    if hidden:
        reply_link_html = '<p class="status-note">This post is hidden by moderation.</p>'
    elif locked:
        reply_link_html = '<p class="status-note">This thread is locked by moderation. New replies are disabled.</p>'
    else:
        reply_link_html = f'<p><a class="thread-chip" href="/compose/reply?thread_id={html.escape(thread_target)}&parent_id={html.escape(post.post_id)}">reply to this post</a></p>'
    content = load_template("post.html").substitute(
        breadcrumb_html=render_breadcrumb(
            [
                ('/', 'board index'),
                ('/threads/' + thread_target, thread_target),
                ('/posts/' + post.post_id, post.post_id),
            ]
        ),
        post_heading=html.escape(heading),
        reply_link_html=reply_link_html,
        post_card_html=render_post_card(
            post,
            root_thread_id=thread_target,
            identity_context=identity_context,
            hidden=hidden,
            compact_thread_view=True,
        ),
    )
    return render_page(
        title=heading,
        hero_kicker="Post Permalink",
        hero_title=heading,
        hero_text="This permalink shows one canonical post in isolation while preserving links back to the thread and board index.",
        content_html=content,
    )


def render_moderation_log_page(*, limit: int, before: str | None) -> str:
    _, _, _, moderation_records, _, identity_context = load_repository_state()
    try:
        records = moderation_log_slice(moderation_records, limit=limit, before=before)
    except ValueError as exc:
        raise PostingError("bad_request", str(exc)) from exc
    entries_html = "".join(render_moderation_card(record, identity_context=identity_context) for record in records)
    if not entries_html:
        entries_html = '<article class="post-card"><p class="post-link">No moderation records are visible yet.</p></article>'
    content = load_template("moderation.html").substitute(
        breadcrumb_html=render_breadcrumb([("/", "board index"), ("/moderation/", "moderation log")]),
        moderation_heading="Moderation Log",
        moderation_text="Signed moderation actions are stored as canonical text records and listed here in deterministic order.",
        entries_html=entries_html,
    )
    return render_page(
        title="Moderation Log",
        hero_kicker="Moderation View",
        hero_title="Signed moderation records",
        hero_text="This log reflects the visible moderation records in the current repository state and provides the audit trail behind public-instance moderation effects.",
        content_html=content,
    )


def render_instance_info_page() -> str:
    repo_root = get_repo_root()
    info = load_instance_info(repo_root)
    content = load_template("instance_info.html").substitute(
        breadcrumb_html=render_breadcrumb([("/", "board index"), ("/instance/", "instance info")]),
        instance_heading=html.escape(render_public_value(info.instance_name)),
        instance_summary=html.escape(
            info.summary
            or "This page publishes the current public operator, policy, and deployment facts for this instance."
        ),
        instance_name=html.escape(render_public_value(info.instance_name)),
        admin_name=html.escape(render_public_value(info.admin_name)),
        admin_contact=html.escape(render_public_value(info.admin_contact)),
        retention_policy=html.escape(render_public_value(info.retention_policy)),
        moderation_settings=html.escape(render_public_value(info.moderation_settings)),
        install_date=html.escape(render_public_value(info.install_date)),
        commit_id=html.escape(render_public_value(info.commit_id)),
        commit_date=html.escape(render_public_value(info.commit_date)),
        source_path=html.escape(str(info.source_path.relative_to(repo_root))),
    )
    return render_page(
        title="Instance Info",
        hero_kicker="Instance View",
        hero_title=render_public_value(info.instance_name),
        hero_text="One public page for current instance-level facts, combining tracked public metadata with derived runtime and repository identity.",
        content_html=content,
    )


def render_profile(identity_id: str) -> str:
    posts, _, _, _, _, identity_context = load_repository_state()
    summary = find_profile_summary(
        repo_root=get_repo_root(),
        posts=posts,
        identity_id=identity_id,
        identity_context=identity_context,
    )
    if summary is None:
        raise LookupError(f"unknown identity: {identity_id}")

    post_links_html = "".join(
        f'<a class="thread-chip" href="/posts/{html.escape(post_id)}">{html.escape(post_id)}</a>'
        for post_id in summary.post_ids
    ) or '<p>No visible signed posts are currently associated with this identity.</p>'
    content = load_template("profile.html").substitute(
        breadcrumb_html=render_breadcrumb(
            [
                ("/", "board index"),
                (f"/profiles/{identity_slug(summary.identity_id)}", summary.display_name),
            ]
        ),
        profile_heading=html.escape(summary.display_name),
        profile_subhead=html.escape(summary.identity_id),
        profile_action_html=(
            f'<a class="thread-chip" href="/profiles/{html.escape(identity_slug(summary.identity_id))}/update">'
            "update username"
            "</a>"
        ),
        stat_html=(
            '<div class="stat-grid">'
            f'<article class="stat-card"><span class="stat-number">{len(summary.member_identity_ids)}</span><span class="stat-label">linked identities</span></article>'
            f'<article class="stat-card"><span class="stat-number">{len(summary.post_ids)}</span><span class="stat-label">visible posts</span></article>'
            f'<article class="stat-card"><span class="stat-number">{len(summary.thread_ids)}</span><span class="stat-label">threads touched</span></article>'
            "</div>"
        ),
        bootstrap_identity_id=html.escape(summary.identity_id),
        bootstrap_source_identity_id=html.escape(summary.bootstrap_identity_id),
        bootstrap_fingerprint=html.escape(summary.signer_fingerprint),
        display_name=html.escape(summary.display_name),
        display_name_source=html.escape(summary.display_name_source),
        fallback_display_name=html.escape(summary.fallback_display_name),
        bootstrap_post_id=html.escape(summary.bootstrap_post_id),
        bootstrap_thread_id=html.escape(summary.bootstrap_thread_id),
        bootstrap_path=html.escape(summary.bootstrap_path),
        public_key_text=html.escape(summary.public_key_text),
        member_identity_html="".join(
            f'<a class="thread-chip" href="/profiles/{html.escape(identity_slug(member_identity_id))}">{html.escape(member_identity_id)}</a>'
            for member_identity_id in summary.member_identity_ids
        ),
        post_links_html=post_links_html,
    )
    return render_page(
        title=summary.display_name,
        hero_kicker="Profile View",
        hero_title=summary.display_name,
        hero_text="This profile view is derived from visible repository records. It resolves linked identities to one canonical profile while preserving the visible bootstrap anchor behind that profile.",
        content_html=content,
    )


def render_profile_update_page(identity_id: str) -> str:
    posts, _, _, _, _, identity_context = load_repository_state()
    summary = find_profile_summary(
        repo_root=get_repo_root(),
        posts=posts,
        identity_id=identity_id,
        identity_context=identity_context,
    )
    if summary is None:
        raise LookupError(f"unknown identity: {identity_id}")

    profile_slug = identity_slug(summary.identity_id)
    content = load_template("profile_update.html").substitute(
        breadcrumb_html=render_breadcrumb(
            [
                ("/", "board index"),
                (f"/profiles/{profile_slug}", summary.display_name),
                (f"/profiles/{profile_slug}/update", "update username"),
            ]
        ),
        update_heading="Update username",
        update_subhead=summary.identity_id,
        current_display_name=html.escape(summary.display_name),
        identity_id=html.escape(summary.identity_id),
        display_name_source=html.escape(summary.display_name_source),
        context_text=html.escape(
            "This dedicated page prepares a signed display-name update for the current resolved identity. "
            "The same canonical profile page remains the readback surface after submission."
        ),
        dry_run_value="false",
        source_identity_id=html.escape(summary.identity_id),
        profile_slug=html.escape(profile_slug),
        display_name_value=html.escape(summary.display_name),
        submit_label="Sign and submit",
    )
    return render_page(
        title=f"Update username · {summary.display_name}",
        hero_kicker="Profile Update",
        hero_title="Update your username",
        hero_text="Use the existing browser signing flow to prepare one signed username/display-name update for the resolved profile you are viewing.",
        content_html=content,
        page_script_html='<script type="module" src="/assets/browser_signing.js"></script>',
    )


def render_post_card(post, *, root_thread_id: str, identity_context, hidden: bool = False, compact_thread_view: bool = False, show_subject: bool = True) -> str:
    subject_html = ""
    if show_subject and post.subject:
        subject_html = f'<h3 class="post-subject">{html.escape(post.subject)}</h3>'

    relation_html = ""
    if not compact_thread_view and not post.is_root:
        relation_html = (
            f'<p class="post-relation">thread <a href="/threads/{html.escape(root_thread_id)}">{html.escape(root_thread_id)}</a>'
            f' · parent <a href="/posts/{html.escape(post.parent_id or "")}">{html.escape(post.parent_id or "")}</a></p>'
        )

    identity_html = ""
    if post.identity_id and post.signer_fingerprint:
        canonical_identity_id = resolved_profile_identity_id(identity_context, post.identity_id)
        display_name = resolve_identity_display_name(
            identity_context=identity_context,
            identity_id=post.identity_id,
            fallback_display_name=short_identity_label(post.signer_fingerprint),
        )
        identity_html = (
            f'<p class="post-identity">signed by <a href="/profiles/{html.escape(identity_slug(canonical_identity_id or post.identity_id))}">'
            f'{html.escape(display_name)}</a></p>'
        )

    body_html = (
        '<div class="post-body"><p class="moderation-note">This post is hidden by moderation.</p></div>'
        if hidden
        else f'<div class="post-body">{render_body_html(post.body)}</div>'
    )
    hidden_class = " post-card--hidden" if hidden else ""
    meta_html = ""
    if not compact_thread_view:
        board_tags = " ".join("/" + html.escape(tag) + "/" for tag in post.board_tags)
        timestamp_label = html.escape(format_post_timestamp(post.post_id))
        meta_html = (
            '<div class="post-meta-row">'
            f'<p class="post-id">{html.escape(post.post_id)}</p>'
            f'<p class="post-tags">{board_tags}</p>'
            f'<p class="post-timestamp">{timestamp_label}</p>'
            "</div>"
        )
    permalink_label = format_post_permalink_label(post.post_id)

    return (
        f'<article class="post-card{hidden_class}">'
        f"{meta_html}"
        f"{subject_html}"
        f"{identity_html}"
        f"{relation_html}"
        f"{body_html}"
        f'<p class="post-link"><a href="/posts/{html.escape(post.post_id)}">{html.escape(permalink_label)}</a></p>'
        "</article>"
    )


def format_post_permalink_label(post_id: str) -> str:
    match = re.search(r"-(\d{14})-", post_id)
    if match is None:
        return "View post"
    try:
        timestamp = datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
    except ValueError:
        return "View post"
    return timestamp.strftime("%b %d, %Y at %H:%M")


def format_post_timestamp(post_id: str) -> str:
    match = re.search(r"-(\d{14})-", post_id)
    if match is None:
        return "unknown date"
    try:
        timestamp = datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
    except ValueError:
        return "unknown date"
    return timestamp.strftime("%B %d, %Y · %H:%M:%S UTC")


def render_compose_reference(post, *, root_thread_id: str, identity_context) -> str:
    return (
        '<section class="panel compose-reference">'
        '<div class="section-head">'
        "<h2>Replying to</h2>"
        "<p>This is the visible post your signed reply will target.</p>"
        "</div>"
        f"{render_post_card(post, root_thread_id=root_thread_id, identity_context=identity_context, compact_thread_view=True)}"
        "</section>"
    )


def render_moderation_card(record, *, identity_context) -> str:
    target_href = f"/threads/{html.escape(record.target_id)}" if record.target_type == "thread" else f"/posts/{html.escape(record.target_id)}"
    moderator_html = ""
    if record.identity_id and record.signer_fingerprint:
        canonical_identity_id = resolved_profile_identity_id(identity_context, record.identity_id)
        display_name = resolve_identity_display_name(
            identity_context=identity_context,
            identity_id=record.identity_id,
            fallback_display_name=short_identity_label(record.signer_fingerprint),
        )
        moderator_html = (
            f'<p class="post-identity">moderated by <a href="/profiles/{html.escape(identity_slug(canonical_identity_id or record.identity_id))}">'
            f'{html.escape(display_name)}</a></p>'
        )
    reason_html = (
        f'<div class="post-body">{render_body_html(record.reason)}</div>'
        if record.reason
        else '<div class="post-body"><p>No reason text was provided.</p></div>'
    )
    return (
        '<article class="post-card moderation-card">'
        '<div class="post-meta-row">'
        f'<p class="post-id">{html.escape(record.record_id)}</p>'
        f'<p class="post-tags">{html.escape(record.timestamp)}</p>'
        "</div>"
        f'<h3 class="post-subject">{html.escape(record.action)} {html.escape(record.target_type)}</h3>'
        f'<p class="post-relation">target <a href="{target_href}">{html.escape(record.target_id)}</a></p>'
        f"{moderator_html}"
        f"{reason_html}"
        "</article>"
    )


def render_body_html(body: str) -> str:
    lines = body.splitlines() or [""]
    rendered = []
    for line in lines:
        escaped = html.escape(line)
        if line.startswith(">"):
            rendered.append(f'<p class="quote-line">{escaped}</p>')
        else:
            rendered.append(f"<p>{escaped}</p>")
    return "".join(rendered)


def render_breadcrumb(items: list[tuple[str, str]]) -> str:
    links = "".join(
        f'<a href="{html.escape(path)}">{html.escape(label)}</a>'
        for path, label in items
    )
    return f'<nav class="breadcrumb">{links}</nav>'


def first_line(body: str) -> str:
    return body.splitlines()[0] if body.splitlines() else ""


def render_task_dependency_targets(
    dependencies: tuple[str, ...],
    *,
    href_prefix: str,
) -> str:
    if not dependencies:
        return "None"
    return ", ".join(
        f'<a href="{html.escape(href_prefix + dependency)}">{html.escape(dependency)}</a>'
        for dependency in dependencies
    )


def render_task_dependency_links(
    dependencies: tuple[str, ...],
    *,
    href_prefix: str = "/planning/tasks/",
) -> str:
    return f'<p class="dep-list">{render_task_dependency_targets(dependencies, href_prefix=href_prefix)}</p>'


def render_task_source_targets(sources: tuple[str, ...]) -> str:
    if not sources:
        return "None"
    return "".join(f"<code>{html.escape(source)}</code>" for source in sources)


def render_task_source_list(sources: tuple[str, ...]) -> str:
    return f'<p class="source-list">{render_task_source_targets(sources)}</p>'


def render_thread_root_context(thread) -> str:
    if not is_task_root(thread.root):
        return ""

    task = thread.root.task_metadata
    assert task is not None
    return (
        '<div class="task-thread-context">'
        '<div class="section-head"><h3>Task metadata</h3>'
        '<p>This typed root post is the current task record. Replies in this thread are task comments.</p></div>'
        '<div class="stat-grid">'
        f'<article class="stat-card"><span class="stat-number">{html.escape(task.status)}</span><span class="stat-label">status</span></article>'
        f'<article class="stat-card"><span class="stat-number">{task.presentability_impact:.2f}</span><span class="stat-label">presentability impact</span></article>'
        f'<article class="stat-card"><span class="stat-number">{task.implementation_difficulty:.2f}</span><span class="stat-label">implementation difficulty</span></article>'
        "</div>"
        '<div class="profile-grid">'
        f'<div><strong>Dependencies:</strong> {render_task_dependency_links(task.dependencies, href_prefix="/threads/")}</div>'
        f'<div><strong>Sources:</strong> {render_task_source_list(task.sources)}</div>'
        "</div>"
        "</div>"
    )


def render_not_found() -> str:
    return render_page(
        title="Not Found",
        hero_kicker="Missing route",
        hero_title="Nothing is published here yet",
        hero_text="This reader publishes a board index, thread pages, and post permalinks. The requested route did not match any known resource.",
        content_html='<section class="panel"><p>Available now: <a href="/">board index</a>. Thread pages live at <code>/threads/{thread-id}</code> and posts at <code>/posts/{post-id}</code>.</p></section>',
    )


def render_missing_resource(resource_name: str) -> str:
    return render_page(
        title="Not Found",
        hero_kicker="Missing resource",
        hero_title="This record could not be located",
        hero_text=f"The requested {resource_name} does not exist in the current repository state.",
        content_html='<section class="panel"><p>Return to the <a href="/">board index</a> to browse available threads.</p></section>',
    )

def is_task_open(thread) -> bool:
    task = thread.root.task_metadata
    assert task is not None
    return task.status.strip().lower() != "done"


def filter_task_threads(task_threads, *, mode: str):
    if mode == "done":
        return [thread for thread in task_threads if not is_task_open(thread)]
    if mode == "all":
        return list(task_threads)
    return [thread for thread in task_threads if is_task_open(thread)]


def task_filter_mode_from_request(raw_mode: str | None) -> str:
    mode = (raw_mode or "").strip().lower()
    if mode in {"done", "all"}:
        return mode
    return "open"


def render_task_filter_nav(*, current_mode: str) -> str:
    links = [
        ("open", "/planning/task-priorities/", "open tasks"),
        ("done", "/planning/task-priorities/?view=done", "done tasks"),
        ("all", "/planning/task-priorities/?view=all", "all tasks"),
    ]
    parts = []
    for mode, href, label in links:
        classes = "thread-chip"
        if mode == current_mode:
            classes += " thread-chip-active"
        parts.append(f'<a class="{classes}" href="{href}">{html.escape(label)}</a>')
    return "".join(parts)


def render_task_priorities_page(*, view_mode: str) -> str:
    _, grouped_threads, _, _, moderation_state, _ = load_repository_state()
    task_threads = load_task_threads(grouped_threads, moderation_state)
    filtered_threads = filter_task_threads(task_threads, mode=view_mode)
    total_comments = sum(visible_reply_count(thread, moderation_state) for thread in task_threads)
    dependency_count = sum(len(thread.root.task_metadata.dependencies) for thread in task_threads if thread.root.task_metadata)
    stats_html = (
        '<div class="stat-grid">'
        f'<article class="stat-card"><span class="stat-number">{len(task_threads)}</span><span class="stat-label">task threads</span></article>'
        f'<article class="stat-card"><span class="stat-number">{total_comments}</span><span class="stat-label">visible task comments</span></article>'
        f'<article class="stat-card"><span class="stat-number">{dependency_count}</span><span class="stat-label">dependency edges</span></article>'
        "</div>"
    )
    rows_html = "".join(
        render_task_priorities_row(thread, moderation_state=moderation_state)
        for thread in filtered_threads
    )
    if not rows_html:
        rows_html = (
            '<tr><td colspan="7"><p class="discussion-note">'
            "No tasks match this view yet."
            "</p></td></tr>"
        )

    table_heading = "Open task table"
    intro_text = (
        "The default view shows open tasks. Switch to done or all-task views as needed, "
        "and use the table headers to sort without changing the canonical repository order."
    )
    table_text = (
        "Dependencies link to task-detail routes in this page. The comments column points back to "
        "the canonical task thread because replies are the discussion surface."
    )
    if view_mode == "done":
        table_heading = "Done task table"
        intro_text = (
            "This view shows completed tasks only. Use the chips below to move between open, done, "
            "and all-task planning views."
        )
    elif view_mode == "all":
        table_heading = "All task table"
        intro_text = (
            "This view shows every task regardless of status. Use the chips below to move between "
            "open, done, and all-task planning views."
        )

    content = load_template("task_priorities.html").substitute(
        stats_html=stats_html,
        rows_html=rows_html,
        intro_text=html.escape(intro_text),
        table_heading=html.escape(table_heading),
        table_text=html.escape(table_text),
        view_nav_html=render_task_filter_nav(current_mode=view_mode),
    )
    return render_page(
        title="Development Task Priorities",
        hero_kicker="Planning View",
        hero_title="Development task priorities",
        hero_text="This planning index is derived from typed task thread roots in `records/posts/`. The root post carries the current task metadata, and ordinary replies are the task comments.",
        content_html=content,
        page_script_html='<script src="/assets/task_priorities.js"></script>',
        page_shell_class="page-shell-wide",
    )


def render_task_priorities_row(thread, *, moderation_state) -> str:
    task = thread.root.task_metadata
    assert task is not None
    discussion_html, discussion_sort_value = render_task_thread_summary(thread, moderation_state=moderation_state)
    dependency_html = render_task_dependency_links(task.dependencies)
    return (
        f'<tr id="task-{html.escape(thread.root.post_id)}"'
        f' data-id="{html.escape(thread.root.post_id)}"'
        f' data-task="{html.escape(thread.root.subject or thread.root.post_id)}"'
        f' data-impact="{task.presentability_impact:.2f}"'
        f' data-difficulty="{task.implementation_difficulty:.2f}"'
        f' data-dependencies="{html.escape(" ".join(task.dependencies))}"'
        f' data-source="{html.escape(" ".join(task.sources))}"'
        f' data-comments="{html.escape(discussion_sort_value)}">'
        f'<td><a class="task-id" href="/planning/tasks/{html.escape(thread.root.post_id)}">{html.escape(thread.root.post_id)}</a></td>'
        "<td>"
        f'<h3 class="task-title"><a class="task-link" href="/planning/tasks/{html.escape(thread.root.post_id)}">{html.escape(thread.root.subject or thread.root.post_id)}</a></h3>'
        f'<p class="task-note">{html.escape(thread.root.body)}</p>'
        f'<p class="task-status">status {html.escape(task.status)}</p>'
        "</td>"
        f'<td><span class="rating-value">{task.presentability_impact:.2f}</span></td>'
        f'<td><span class="rating-value">{task.implementation_difficulty:.2f}</span></td>'
        f"<td>{dependency_html}</td>"
        f'<td>{render_task_source_list(task.sources)}</td>'
        f"<td>{discussion_html}</td>"
        "</tr>"
    )


def render_task_thread_summary(thread, *, moderation_state) -> tuple[str, str]:
    reply_count = visible_reply_count(thread, moderation_state)
    labels = thread_status_labels(thread.root.post_id, moderation_state)
    suffix = ""
    if labels:
        suffix = " · " + " ".join(labels)
    return (
        '<p class="discussion-note">'
        f'<a href="/threads/{html.escape(thread.root.post_id)}">{html.escape(thread.root.post_id)}</a>'
        f' · {reply_count} visible repl{"y" if reply_count == 1 else "ies"}{suffix}'
        "</p>",
        f"{reply_count:04d}",
    )


def render_task_completion_feedback(
    result: TaskStatusUpdateResult | None = None,
    *,
    error_message: str | None = None,
) -> str:
    if result is not None:
        return (
            '<section class="panel">'
            '<div class="section-head"><h2>Task updated</h2>'
            f"<p>Status changed from {html.escape(result.previous_status)} to done.</p></div>"
            f'<p><strong>Commit:</strong> <code>{html.escape(result.commit_id)}</code></p>'
            '<div class="action-row">'
            '<a class="thread-chip" href="/planning/task-priorities/">open tasks</a>'
            '<a class="thread-chip" href="/planning/task-priorities/?view=done">done tasks</a>'
            '<a class="thread-chip" href="/planning/task-priorities/?view=all">all tasks</a>'
            "</div>"
            "</section>"
        )
    if error_message:
        return (
            '<section class="panel">'
            '<div class="section-head"><h2>Task update failed</h2>'
            f"<p>{html.escape(error_message)}</p></div>"
            "</section>"
        )
    return ""


def render_task_status_action(thread) -> str:
    task = thread.root.task_metadata
    assert task is not None
    if task.status.strip().lower() == "done":
        return (
            '<p class="discussion-note">This task is already marked done.</p>'
            '<div class="action-row">'
            '<a class="thread-chip" href="/planning/task-priorities/?view=done">view done tasks</a>'
            "</div>"
        )
    return (
        f'<form method="post" action="/planning/tasks/{html.escape(thread.root.post_id)}/mark-done" class="field-stack">'
        '<button type="submit">mark task done</button>'
        "</form>"
    )


def render_task_detail_page(
    task_id: str,
    *,
    completion_result: TaskStatusUpdateResult | None = None,
    completion_error: str | None = None,
) -> str:
    _, grouped_threads, _, _, moderation_state, _ = load_repository_state()
    task_threads = load_task_threads(grouped_threads, moderation_state)
    thread = index_task_threads(task_threads).get(task_id)
    if thread is None:
        raise LookupError(f"unknown task: {task_id}")

    task = thread.root.task_metadata
    assert task is not None
    discussion_html = render_task_detail_discussion(thread, moderation_state=moderation_state)
    content = load_template("task_detail.html").substitute(
        breadcrumb_html=render_breadcrumb(
            [
                ("/", "board index"),
                ("/planning/task-priorities/", "task priorities"),
                (f"/planning/tasks/{thread.root.post_id}", thread.root.post_id),
            ]
        ),
        task_heading=html.escape(thread.root.subject or thread.root.post_id),
        task_id=html.escape(thread.root.post_id),
        task_status=html.escape(task.status),
        task_summary=html.escape(thread.root.body),
        task_impact=f"{task.presentability_impact:.2f}",
        task_difficulty=f"{task.implementation_difficulty:.2f}",
        dependency_html=render_task_dependency_links(task.dependencies),
        source_html=render_task_source_targets(task.sources),
        completion_feedback_html=render_task_completion_feedback(
            completion_result,
            error_message=completion_error,
        ),
        task_status_action_html=render_task_status_action(thread),
        discussion_html=discussion_html,
    )
    return render_page(
        title=thread.root.subject or thread.root.post_id,
        hero_kicker="Task Detail",
        hero_title=thread.root.subject or thread.root.post_id,
        hero_text="This task view is derived from one task-typed root thread. The root carries structured task metadata, and the same thread remains the discussion surface.",
        content_html=content,
    )


def render_task_detail_discussion(thread, *, moderation_state) -> str:
    reply_count = visible_reply_count(thread, moderation_state)
    thread_labels = thread_status_labels(thread.root.post_id, moderation_state)
    status_text = " ".join(thread_labels) if thread_labels else "open"
    reply_link_html = (
        f'<a class="thread-chip" href="/compose/reply?thread_id={html.escape(thread.root.post_id)}&parent_id={html.escape(thread.root.post_id)}">reply on this task</a>'
        if not moderation_state.locks_thread(thread.root.post_id)
        else '<p class="discussion-note">This task thread is locked by moderation.</p>'
    )
    return (
        '<section class="panel">'
        '<div class="section-head"><h2>Discussion</h2>'
        '<p>This task thread is also the discussion thread. Replies stay in the normal forum reply flow.</p></div>'
        '<div class="stat-grid">'
        f'<article class="stat-card"><span class="stat-number">{reply_count}</span><span class="stat-label">visible replies</span></article>'
        f'<article class="stat-card"><span class="stat-number">{html.escape(status_text)}</span><span class="stat-label">thread state</span></article>'
        f'<article class="stat-card"><span class="stat-number">{html.escape(thread.root.post_id)}</span><span class="stat-label">thread id</span></article>'
        "</div>"
        f'<p class="task-note task-note--detail">{html.escape(first_line(thread.root.body))}</p>'
        '<div class="action-row">'
        f'<a class="thread-chip" href="/threads/{html.escape(thread.root.post_id)}">open task thread</a>'
        f"{reply_link_html}"
        "</div>"
        "</section>"
    )


def render_api_home() -> str:
    repo_root = get_repo_root()
    posts, threads, board_tags, _, moderation_state, _ = load_repository_state()
    return render_api_home_text(
        post_count=len(posts),
        thread_count=len(visible_threads(threads, moderation_state, repo_root=repo_root)),
        board_tags=board_tags,
    )


def render_api_list_index(board_tag: str | None) -> str:
    repo_root = get_repo_root()
    _, threads, board_tags, _, moderation_state, _ = load_repository_state()
    if board_tag and board_tag not in board_tags:
        return render_bad_request_text(f"unknown board_tag: {board_tag}")

    public_threads = visible_threads(threads, moderation_state, board_tag=board_tag, repo_root=repo_root)
    reply_counts = {
        thread.root.post_id: visible_reply_count(thread, moderation_state)
        for thread in public_threads
    }
    return render_index_text(
        public_threads,
        board_tag=board_tag,
        visible_reply_counts=reply_counts,
        pinned_thread_ids=moderation_state.pinned_thread_ids,
        locked_thread_ids=moderation_state.locked_thread_ids,
    )


def render_api_get_thread(thread_id: str | None) -> tuple[str, str]:
    if not thread_id:
        return "400 Bad Request", render_bad_request_text("missing required query parameter: thread_id")

    _, grouped_threads, _, _, moderation_state, _ = load_repository_state()
    thread = index_threads(grouped_threads).get(thread_id)
    if thread is None or thread_is_hidden(moderation_state, thread_id):
        return "404 Not Found", render_not_found_text("thread", thread_id)

    hidden_post_ids = frozenset(
        reply.post_id
        for reply in thread.replies
        if post_is_hidden(moderation_state, reply.post_id, thread.root.post_id)
    )
    return "200 OK", render_thread_text(
        thread,
        hidden_post_ids=hidden_post_ids,
        locked=moderation_state.locks_thread(thread_id),
    )


def render_api_get_post(post_id: str | None) -> tuple[str, str]:
    if not post_id:
        return "400 Bad Request", render_bad_request_text("missing required query parameter: post_id")

    posts, _, _, _, moderation_state, _ = load_repository_state()
    post = index_posts(posts).get(post_id)
    if post is None:
        return "404 Not Found", render_not_found_text("post", post_id)
    if thread_is_hidden(moderation_state, post.root_thread_id):
        return "404 Not Found", render_not_found_text("post", post_id)

    return "200 OK", render_post_text(
        post,
        hidden=post_is_hidden(moderation_state, post.post_id, post.root_thread_id),
    )


def render_api_get_profile(identity_id: str | None) -> tuple[str, str]:
    if not identity_id:
        return "400 Bad Request", render_bad_request_text("missing required query parameter: identity_id")

    posts, _, _, _, _, identity_context = load_repository_state()
    summary = find_profile_summary(
        repo_root=get_repo_root(),
        posts=posts,
        identity_id=identity_id,
        identity_context=identity_context,
    )
    if summary is None:
        return "404 Not Found", render_not_found_text("identity", identity_id)

    return "200 OK", render_profile_text(summary)


def render_api_get_moderation_log(limit: int, before: str | None) -> tuple[str, str]:
    _, _, _, moderation_records, _, _ = load_repository_state()
    try:
        records = moderation_log_slice(moderation_records, limit=limit, before=before)
    except ValueError as exc:
        return "400 Bad Request", render_bad_request_text(str(exc))
    return "200 OK", render_moderation_log_text(records, limit=limit, before=before)


def normalize_board_tags_text(raw_text: str) -> str:
    tags = [tag for tag in raw_text.split() if tag]
    return " ".join(tags) or "general"


def describe_board_tags(board_tags: str) -> str:
    return " ".join(f"/{tag}/" for tag in board_tags.split())


def render_task_compose_fields() -> str:
    return (
        '<section class="compose-card task-compose-fields">'
        '<div class="section-head"><h2>Task metadata</h2>'
        '<p>This root post becomes the current task record for the thread. Future task-state history can move into task-update records without changing the reply model.</p></div>'
        '<div class="field-grid">'
        '<label class="field-stack" for="task-status-input"><span>Task status</span><input id="task-status-input" name="task_status" type="text" value="proposed" maxlength="40" required></label>'
        '<label class="field-stack" for="task-impact-input"><span>Presentability impact</span><input id="task-impact-input" name="task_impact" type="number" min="0" max="1" step="0.01" value="0.50" required></label>'
        '<label class="field-stack" for="task-difficulty-input"><span>Implementation difficulty</span><input id="task-difficulty-input" name="task_difficulty" type="number" min="0" max="1" step="0.01" value="0.50" required></label>'
        '<label class="field-stack" for="task-dependencies-input"><span>Dependencies</span><input id="task-dependencies-input" name="task_dependencies" type="text" value="" placeholder="T01 T02"></label>'
        '<label class="field-stack field-grid-span" for="task-sources-input"><span>Sources</span><input id="task-sources-input" name="task_sources" type="text" value="" placeholder="todo.txt; ideas.txt"></label>'
        "</div>"
        "</section>"
    )


def render_compose_page(
    *,
    command_name: str,
    endpoint_path: str,
    compose_heading: str,
    compose_text: str,
    dry_run: bool,
    board_tags: str,
    context_text: str,
    thread_id: str = "",
    parent_id: str = "",
    reply_target_html: str = "",
    compose_path: str = "",
    breadcrumb_label: str = "signed compose",
    thread_type: str = "",
    extra_fields_html: str = "",
) -> str:
    content = load_template("compose.html").substitute(
        compose_heading=html.escape(compose_heading),
        compose_text=html.escape(compose_text),
        context_text=html.escape(context_text),
        reply_target_html=reply_target_html,
        command_name=html.escape(command_name),
        endpoint_path=html.escape(endpoint_path),
        dry_run_value="true" if dry_run else "false",
        board_tags_value=html.escape(board_tags),
        thread_id_value=html.escape(thread_id),
        parent_id_value=html.escape(parent_id),
        thread_type_value=html.escape(thread_type),
        pow_enabled_value="true" if first_post_pow_enabled() else "false",
        pow_difficulty_value=str(first_post_pow_difficulty()),
        body_value="",
        extra_fields_html=extra_fields_html,
        submit_label="Sign and preview" if dry_run else "Sign and submit",
    )
    return render_page(
        title=compose_heading,
        hero_kicker="Signed Posting",
        hero_title=compose_heading,
        hero_text=compose_text,
        content_html=content,
        page_header_html=render_site_header(
            hero_kicker="Signed Posting",
            hero_title=compose_heading,
            hero_text=compose_text,
            include_page_intro=False,
        ),
        page_script_html='<script type="module" src="/assets/browser_signing.js"></script>',
    )


def read_json_request(environ) -> dict[str, object]:
    content_length = environ.get("CONTENT_LENGTH", "").strip()
    if not content_length:
        raise PostingError("bad_request", "missing request body")
    try:
        raw_length = int(content_length)
    except ValueError as exc:
        raise PostingError("bad_request", "invalid content length") from exc

    raw_body = environ["wsgi.input"].read(raw_length)
    if not raw_body:
        raise PostingError("bad_request", "missing request body")
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PostingError("bad_request", "request body must be UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise PostingError("bad_request", "request body must be a JSON object")
    return payload


def parse_dry_run_flag(value, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    raise PostingError("bad_request", "dry_run must be a boolean")


def read_optional_text(payload: dict[str, object], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise PostingError("bad_request", f"{field_name} must be a string")
    return value if value != "" else None


def read_required_text(payload: dict[str, object], field_name: str) -> str:
    value = read_optional_text(payload, field_name)
    if value is None or not value.strip():
        raise PostingError("bad_request", f"missing required field: {field_name}")
    return value.strip()


def build_llm_messages(*, prompt: str, system_prompt: str | None = None) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return messages


def render_api_call_llm(environ) -> tuple[str, str]:
    try:
        payload = read_json_request(environ)
        prompt = read_required_text(payload, "prompt")
        system_prompt = read_optional_text(payload, "system_prompt")
    except PostingError as exc:
        return "400 Bad Request", render_error_body(exc.error_code, exc.message)

    try:
        output_text = run_llm(
            build_llm_messages(
                prompt=prompt,
                system_prompt=system_prompt.strip() if system_prompt else None,
            )
        )
    except LLMProviderError as exc:
        message = str(exc)
        if message in {
            "DEDALUS_API_KEY is not configured.",
            "Dedalus SDK not installed. Add 'dedalus-labs' to requirements.",
        }:
            return "500 Internal Server Error", render_error_body("internal_error", message)
        return "502 Bad Gateway", render_error_body("upstream_error", message)

    return "200 OK", render_llm_result_text(model=get_llm_model(), output_text=output_text)


def render_api_create_thread(environ, *, default_dry_run: bool) -> tuple[str, str]:
    payload = read_json_request(environ)
    repo_root = get_repo_root()
    result = submit_create_thread(
        read_optional_text(payload, "payload") or "",
        repo_root,
        dry_run=parse_dry_run_flag(payload.get("dry_run"), default=default_dry_run),
        signature_text=read_optional_text(payload, "signature"),
        public_key_text=read_optional_text(payload, "public_key"),
        require_signature=True,
    )
    return "200 OK", render_submission_result(result)


def render_api_create_reply(environ, *, default_dry_run: bool) -> tuple[str, str]:
    payload = read_json_request(environ)
    repo_root = get_repo_root()
    result = submit_create_reply(
        read_optional_text(payload, "payload") or "",
        repo_root,
        dry_run=parse_dry_run_flag(payload.get("dry_run"), default=default_dry_run),
        signature_text=read_optional_text(payload, "signature"),
        public_key_text=read_optional_text(payload, "public_key"),
        require_signature=True,
    )
    return "200 OK", render_submission_result(result)


def render_api_pow_requirement(environ) -> tuple[str, bytes, str]:
    payload = read_json_request(environ)
    repo_root = get_repo_root()
    public_key_text = read_required_text(payload, "public_key")

    signer_fingerprint, required = pow_requirement_for_public_key(
        repo_root=repo_root,
        public_key_text=public_key_text,
    )
    body = json.dumps(
        {
            "required": first_post_pow_enabled() and required,
            "difficulty": first_post_pow_difficulty(),
            "signer_fingerprint": signer_fingerprint,
        }
    ).encode("utf-8")
    return "200 OK", body, "application/json; charset=utf-8"


def render_api_moderate(environ, *, default_dry_run: bool) -> tuple[str, str]:
    payload = read_json_request(environ)
    repo_root = get_repo_root()
    result = submit_moderation(
        read_optional_text(payload, "payload") or "",
        repo_root,
        dry_run=parse_dry_run_flag(payload.get("dry_run"), default=default_dry_run),
        signature_text=read_optional_text(payload, "signature"),
        public_key_text=read_optional_text(payload, "public_key"),
        require_signature=True,
    )
    return "200 OK", render_moderation_result(result)


def render_api_link_identity(environ, *, default_dry_run: bool) -> tuple[str, str]:
    payload = read_json_request(environ)
    repo_root = get_repo_root()
    result = submit_identity_link(
        read_optional_text(payload, "payload") or "",
        repo_root,
        dry_run=parse_dry_run_flag(payload.get("dry_run"), default=default_dry_run),
        signature_text=read_optional_text(payload, "signature"),
        public_key_text=read_optional_text(payload, "public_key"),
        require_signature=True,
    )
    return "200 OK", render_identity_link_result(result)


def render_api_update_profile(environ, *, default_dry_run: bool) -> tuple[str, str]:
    payload = read_json_request(environ)
    repo_root = get_repo_root()
    result = submit_profile_update(
        read_optional_text(payload, "payload") or "",
        repo_root,
        dry_run=parse_dry_run_flag(payload.get("dry_run"), default=default_dry_run),
        signature_text=read_optional_text(payload, "signature"),
        public_key_text=read_optional_text(payload, "public_key"),
        require_signature=True,
    )
    return "200 OK", render_profile_update_result(result)


def application(environ, start_response):
    setup_testing_defaults(environ)
    path = environ.get("PATH_INFO", "/")
    query_params = parse_qs(environ.get("QUERY_STRING", ""))
    method = environ.get("REQUEST_METHOD", "GET").upper()

    try:
        if path == "/api/create_thread":
            if method != "POST":
                body = render_error_body("bad_request", "POST is required").encode("utf-8")
                headers = [("Content-Type", "text/plain; charset=utf-8")]
                start_response("405 Method Not Allowed", headers)
                return [body]
            status, body_text = render_api_create_thread(environ, default_dry_run=False)
            body = body_text.encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, headers)
            return [body]

        if path == "/api/create_reply":
            if method != "POST":
                body = render_error_body("bad_request", "POST is required").encode("utf-8")
                headers = [("Content-Type", "text/plain; charset=utf-8")]
                start_response("405 Method Not Allowed", headers)
                return [body]
            status, body_text = render_api_create_reply(environ, default_dry_run=False)
            body = body_text.encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, headers)
            return [body]

        if path == "/api/pow_requirement":
            if method != "POST":
                body = render_error_body("bad_request", "POST is required").encode("utf-8")
                headers = [("Content-Type", "text/plain; charset=utf-8")]
                start_response("405 Method Not Allowed", headers)
                return [body]
            status, body, content_type = render_api_pow_requirement(environ)
            headers = [("Content-Type", content_type)]
            start_response(status, headers)
            return [body]

        if path == "/api/moderate":
            if method != "POST":
                body = render_error_body("bad_request", "POST is required").encode("utf-8")
                headers = [("Content-Type", "text/plain; charset=utf-8")]
                start_response("405 Method Not Allowed", headers)
                return [body]
            status, body_text = render_api_moderate(environ, default_dry_run=False)
            body = body_text.encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, headers)
            return [body]

        if path == "/api/link_identity":
            if method != "POST":
                body = render_error_body("bad_request", "POST is required").encode("utf-8")
                headers = [("Content-Type", "text/plain; charset=utf-8")]
                start_response("405 Method Not Allowed", headers)
                return [body]
            status, body_text = render_api_link_identity(environ, default_dry_run=False)
            body = body_text.encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, headers)
            return [body]

        if path == "/api/update_profile":
            if method != "POST":
                body = render_error_body("bad_request", "POST is required").encode("utf-8")
                headers = [("Content-Type", "text/plain; charset=utf-8")]
                start_response("405 Method Not Allowed", headers)
                return [body]
            status, body_text = render_api_update_profile(environ, default_dry_run=False)
            body = body_text.encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, headers)
            return [body]

        if path == "/api/call_llm":
            if method != "POST":
                body = render_error_body("bad_request", "POST is required").encode("utf-8")
                headers = [("Content-Type", "text/plain; charset=utf-8")]
                start_response("405 Method Not Allowed", headers)
                return [body]
            status, body_text = render_api_call_llm(environ)
            body = body_text.encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, headers)
            return [body]

        if path == "/api/":
            body = render_api_home().encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/api/list_index":
            board_tag = query_params.get("board_tag", [""])[0].strip() or None
            body_text = render_api_list_index(board_tag)
            status = "200 OK"
            if body_text.startswith("Error-Code: bad_request"):
                status = "400 Bad Request"
            body = body_text.encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, headers)
            return [body]

        if path == "/api/get_thread":
            thread_id = query_params.get("thread_id", [""])[0].strip() or None
            status, body_text = render_api_get_thread(thread_id)
            body = body_text.encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, headers)
            return [body]

        if path == "/api/get_post":
            post_id = query_params.get("post_id", [""])[0].strip() or None
            status, body_text = render_api_get_post(post_id)
            body = body_text.encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, headers)
            return [body]

        if path == "/api/get_profile":
            identity_id = query_params.get("identity_id", [""])[0].strip() or None
            status, body_text = render_api_get_profile(identity_id)
            body = body_text.encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, headers)
            return [body]

        if path == "/api/get_moderation_log":
            limit = parse_limit_value(query_params.get("limit", [""])[0] if "limit" in query_params else None)
            before = query_params.get("before", [""])[0].strip() or None
            status, body_text = render_api_get_moderation_log(limit, before)
            body = body_text.encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, headers)
            return [body]

        if path == "/llms.txt":
            body = render_llms_text().encode("utf-8")
            headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/":
            body = render_board_index().encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/instance/":
            body = render_instance_info_page().encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/activity/":
            view_mode = activity_filter_mode_from_request(query_params.get("view", [""])[0])
            body = render_site_activity_page(view_mode=view_mode).encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/moderation/":
            headers = [
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Location", "/activity/?view=moderation"),
            ]
            start_response("302 Found", headers)
            return [b""]

        if path in {"/planning/task-priorities", "/planning/task-priorities/"}:
            view_mode = task_filter_mode_from_request(query_params.get("view", [""])[0])
            body = render_task_priorities_page(view_mode=view_mode).encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path.startswith("/planning/tasks/") and path.endswith("/mark-done"):
            task_id = unquote(path.removeprefix("/planning/tasks/").removesuffix("/mark-done")).rstrip("/")
            if method != "POST":
                body = render_error_body("bad_request", "POST is required").encode("utf-8")
                headers = [("Content-Type", "text/plain; charset=utf-8")]
                start_response("405 Method Not Allowed", headers)
                return [body]
            try:
                result = submit_mark_task_done(task_id, get_repo_root())
                body = render_task_detail_page(task_id, completion_result=result).encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("200 OK", headers)
                return [body]
            except LookupError:
                body = render_missing_resource("task").encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("404 Not Found", headers)
                return [body]
            except PostingError as exc:
                body = render_task_detail_page(task_id, completion_error=exc.message).encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response(exc.status, headers)
                return [body]

        if path.startswith("/planning/tasks/"):
            task_id = unquote(path.removeprefix("/planning/tasks/")).rstrip("/")
            try:
                body = render_task_detail_page(task_id).encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("200 OK", headers)
                return [body]
            except LookupError:
                body = render_missing_resource("task").encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("404 Not Found", headers)
                return [body]

        if path in {"/compose/thread", "/compose/task"}:
            requested_thread_type = query_params.get("thread_type", [""])[0].strip()
            if path == "/compose/task":
                requested_thread_type = "task"
            default_board = "planning" if requested_thread_type == "task" else "general"
            raw_board_tags = query_params.get("board_tags", [""])[0].strip() or query_params.get("board_tag", [default_board])[0].strip()
            board_tags = normalize_board_tags_text(raw_board_tags)
            if requested_thread_type == "task":
                body = render_compose_page(
                    command_name="create_thread",
                    endpoint_path="/api/create_thread",
                    compose_heading="Compose a signed task thread",
                    compose_text="Generate or import a local OpenPGP key, sign one task-shaped thread root in the browser, and submit it directly into repository storage.",
                    dry_run=False,
                    board_tags=board_tags,
                    context_text=(
                        f"This page will open a new task thread in {describe_board_tags(board_tags)}. "
                        "The root post carries the structured task metadata, and future replies become task comments."
                    ),
                    compose_path="/compose/task",
                    breadcrumb_label="compose task",
                    thread_type="task",
                    extra_fields_html=render_task_compose_fields(),
                ).encode("utf-8")
            else:
                body = render_compose_page(
                    command_name="create_thread",
                    endpoint_path="/api/create_thread",
                    compose_heading="Compose a signed thread",
                    compose_text="Generate or import a local OpenPGP key, sign a canonical thread payload in the browser, and submit the signed thread directly into repository storage.",
                    dry_run=False,
                    board_tags=board_tags,
                    context_text=f"This page will open a new signed thread in {describe_board_tags(board_tags)}. The post ID and thread title are derived automatically from what you write.",
                    compose_path="/compose/thread",
                ).encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/compose/reply":
            thread_id = query_params.get("thread_id", [""])[0].strip()
            parent_id = query_params.get("parent_id", [""])[0].strip()
            if not thread_id:
                body = render_missing_resource("thread").encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("404 Not Found", headers)
                return [body]

            posts, grouped_threads, _, _, moderation_state, identity_context = load_repository_state()
            thread = index_threads(grouped_threads).get(thread_id)
            if thread is None or thread_is_hidden(moderation_state, thread_id):
                body = render_missing_resource("thread").encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("404 Not Found", headers)
                return [body]
            if moderation_state.locks_thread(thread_id):
                body = render_page(
                    title="Thread Locked",
                    hero_kicker="Moderation state",
                    hero_title="This thread is locked",
                    hero_text="A signed moderation action currently prevents new replies in this thread.",
                    content_html='<section class="panel"><p>Return to the <a href="/">board index</a> or the current <a href="/threads/' + html.escape(thread_id) + '">thread view</a>.</p></section>',
                ).encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("409 Conflict", headers)
                return [body]

            posts_by_id = index_posts(posts)
            if not parent_id:
                parent_id = thread.root.post_id
            parent_post = posts_by_id.get(parent_id)
            if (
                parent_post is None
                or parent_post.root_thread_id != thread.root.post_id
                or post_is_hidden(moderation_state, parent_id, thread.root.post_id)
            ):
                body = render_missing_resource("post").encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("404 Not Found", headers)
                return [body]

            board_tags = " ".join(thread.root.board_tags)
            body = render_compose_page(
                command_name="create_reply",
                endpoint_path="/api/create_reply",
                compose_heading="Compose a signed reply",
                compose_text="Generate or import a local OpenPGP key, sign a canonical reply payload in the browser, and submit the signed reply directly into repository storage.",
                dry_run=False,
                board_tags=board_tags,
                context_text=f"This signed reply will go into thread {thread.root.post_id} in {describe_board_tags(board_tags)} under parent {parent_id}. Reply linkage is filled in automatically.",
                thread_id=thread_id,
                parent_id=parent_id,
                compose_path="/compose/reply",
                breadcrumb_label="compose reply",
                reply_target_html=render_compose_reference(
                    parent_post,
                    root_thread_id=thread.root.post_id,
                    identity_context=identity_context,
                ),
            ).encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/assets/site.css":
            body = load_asset_text("site.css").encode("utf-8")
            headers = [("Content-Type", "text/css; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/assets/browser_signing.js":
            body = load_asset_text("browser_signing.js").encode("utf-8")
            headers = [("Content-Type", "text/javascript; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/assets/task_priorities.js":
            body = load_asset_text("task_priorities.js").encode("utf-8")
            headers = [("Content-Type", "text/javascript; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/assets/vendor/openpgp.min.mjs":
            body = load_asset_text("vendor/openpgp.min.mjs").encode("utf-8")
            headers = [("Content-Type", "text/javascript; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path.startswith("/threads/"):
            thread_id = path.removeprefix("/threads/")
            try:
                body = render_thread(thread_id).encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("200 OK", headers)
                return [body]
            except LookupError:
                body = render_missing_resource("thread").encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("404 Not Found", headers)
                return [body]

        if path.startswith("/posts/"):
            post_id = path.removeprefix("/posts/")
            try:
                body = render_post(post_id).encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("200 OK", headers)
                return [body]
            except LookupError:
                body = render_missing_resource("post").encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("404 Not Found", headers)
                return [body]

        if path.startswith("/profiles/") and path.endswith("/update"):
            slug = unquote(path.removeprefix("/profiles/").removesuffix("/update"))
            slug = slug.rstrip("/")
            try:
                identity_id = identity_id_from_slug(slug)
                body = render_profile_update_page(identity_id).encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("200 OK", headers)
                return [body]
            except (LookupError, ValueError):
                body = render_missing_resource("profile").encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("404 Not Found", headers)
                return [body]

        if path.startswith("/profiles/"):
            slug = unquote(path.removeprefix("/profiles/"))
            try:
                identity_id = identity_id_from_slug(slug)
                body = render_profile(identity_id).encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("200 OK", headers)
                return [body]
            except (LookupError, ValueError):
                body = render_missing_resource("profile").encode("utf-8")
                headers = [("Content-Type", "text/html; charset=utf-8")]
                start_response("404 Not Found", headers)
                return [body]

        body = render_not_found().encode("utf-8")
        headers = [("Content-Type", "text/html; charset=utf-8")]
        start_response("404 Not Found", headers)
        return [body]
    except PostingError as exc:
        body = render_error_body(exc.error_code, exc.message).encode("utf-8")
        headers = [("Content-Type", "text/plain; charset=utf-8")]
        start_response(exc.status, headers)
        return [body]
    except Exception as exc:  # pragma: no cover - manual smoke checks cover this path
        body = (
            "<!doctype html><title>Server Error</title>"
            f"<pre>{html.escape(str(exc))}</pre>"
        ).encode("utf-8")
        headers = [("Content-Type", "text/html; charset=utf-8")]
        start_response("500 Internal Server Error", headers)
        return [body]
