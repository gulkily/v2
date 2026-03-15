from __future__ import annotations

import html
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote
from wsgiref.util import setup_testing_defaults

from forum_core.identity import identity_id_from_slug, identity_slug, short_identity_label
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
from forum_cgi.text import (
    render_error_body,
    render_identity_link_result,
    render_moderation_result,
    render_profile_update_result,
    render_submission_result,
)
from forum_read_only.api_text import (
    render_api_home_text,
    render_bad_request_text,
    render_index_text,
    render_moderation_log_text,
    render_not_found_text,
    render_post_text,
    render_profile_text,
    render_thread_text,
)
from forum_read_only.profiles import find_profile_summary, load_identity_context, resolve_identity_display_name
from forum_read_only.repository import (
    group_threads,
    index_posts,
    index_threads,
    list_board_tags,
    load_posts,
)
from forum_read_only.templates import load_asset_text, load_template, render_page

load_repo_env()
notify_missing_env_defaults()


def get_repo_root() -> Path:
    env_root = os.environ.get("FORUM_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parent.parent


def get_app_root() -> Path:
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


def visible_threads(threads, moderation_state, *, board_tag: str | None = None):
    filtered = [
        thread
        for thread in threads
        if not thread_is_hidden(moderation_state, thread.root.post_id)
    ]
    if board_tag:
        filtered = [thread for thread in filtered if board_tag in thread.root.board_tags]
    return sorted(
        filtered,
        key=lambda thread: (
            0 if moderation_state.pins_thread(thread.root.post_id) else 1,
            thread.root.post_id,
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


def render_thread_status_badges(thread_id: str, moderation_state) -> str:
    return "".join(
        f'<span class="thread-badge">{"locked" if label == "locked" else "pinned"}</span>'
        for label in thread_status_labels(thread_id, moderation_state)
    )


def resolved_profile_identity_id(identity_context, identity_id: str | None) -> str | None:
    if identity_id is None:
        return None
    return identity_context.canonical_identity_id(identity_id) or identity_id


def render_board_index() -> str:
    posts, threads, _, _, moderation_state, _ = load_repository_state()
    public_threads = visible_threads(threads, moderation_state)
    board_tags = sorted({tag for thread in public_threads for tag in thread.root.board_tags})
    board_sections = [
        (
            tag,
            tuple(thread for thread in public_threads if tag in thread.root.board_tags),
        )
        for tag in board_tags
    ]

    stats_html = (
        '<div class="stat-grid">'
        f'<article class="stat-card"><span class="stat-number">{len(posts)}</span><span class="stat-label">posts loaded</span></article>'
        f'<article class="stat-card"><span class="stat-number">{len(public_threads)}</span><span class="stat-label">visible threads</span></article>'
        f'<article class="stat-card"><span class="stat-number">{len(board_tags)}</span><span class="stat-label">board tags</span></article>'
        "</div>"
    )

    tag_items = "".join(f'<a class="tag-chip" href="#board-{html.escape(tag)}">{html.escape(tag)}</a>' for tag in board_tags)
    board_sections_html = "".join(
        render_board_section(tag, section_threads, moderation_state)
        for tag, section_threads in board_sections
    )

    content = load_template("board_index.html").substitute(
        stats_html=stats_html,
        tags_html=tag_items,
        board_sections_html=board_sections_html,
    )
    return render_page(
        title="Forum Reader",
        hero_kicker="Board Index",
        hero_title="Threads gathered straight from canonical text records",
        hero_text="This board view reads the git-tracked post files directly, groups thread roots by board tags, and keeps the dataset browsable without adding a database or durable index layer.",
        content_html=content,
    )


def render_board_section(tag: str, threads, moderation_state) -> str:
    thread_cards = "".join(
        "<article class=\"thread-card\">"
        f"{render_thread_status_badges(thread.root.post_id, moderation_state)}"
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
    if thread_labels:
        thread_meta += " " + " ".join(thread_labels) + "."

    content = load_template("thread.html").substitute(
        breadcrumb_html=render_breadcrumb(
            [
                ('/', 'board index'),
                ('/threads/' + thread.root.post_id, thread.root.subject or thread.root.post_id),
            ]
        ),
        thread_heading=html.escape(thread.root.subject or thread.root.post_id),
        thread_meta=thread_meta,
        reply_link_html=reply_link_html,
        root_post_html=render_post_card(
            thread.root,
            root_thread_id=thread.root.post_id,
            identity_context=identity_context,
        ),
        replies_html="".join(
            render_post_card(
                reply,
                root_thread_id=thread.root.post_id,
                identity_context=identity_context,
                hidden=post_is_hidden(moderation_state, reply.post_id, thread.root.post_id),
            )
            for reply in thread.replies
        ),
    )
    return render_page(
        title=thread.root.subject or thread.root.post_id,
        hero_kicker="Thread View",
        hero_title=thread.root.subject or thread.root.post_id,
        hero_text="The thread page is rendered directly from canonical post files without a database, using deterministic reply ordering from the repository state.",
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


def render_post_card(post, *, root_thread_id: str, identity_context, hidden: bool = False) -> str:
    board_tags = " ".join("/" + html.escape(tag) + "/" for tag in post.board_tags)
    subject_html = ""
    if post.subject:
        subject_html = f'<h3 class="post-subject">{html.escape(post.subject)}</h3>'

    relation_html = ""
    if not post.is_root:
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

    return (
        f'<article class="post-card{hidden_class}">'
        '<div class="post-meta-row">'
        f'<p class="post-id">{html.escape(post.post_id)}</p>'
        f'<p class="post-tags">{board_tags}</p>'
        "</div>"
        f"{subject_html}"
        f"{identity_html}"
        f"{relation_html}"
        f"{body_html}"
        f'<p class="post-link"><a href="/posts/{html.escape(post.post_id)}">permalink</a></p>'
        "</article>"
    )


def render_compose_reference(post, *, root_thread_id: str, identity_context) -> str:
    return (
        '<section class="panel compose-reference">'
        '<div class="section-head">'
        "<h2>Replying to</h2>"
        "<p>This is the visible post your signed reply will target.</p>"
        "</div>"
        f"{render_post_card(post, root_thread_id=root_thread_id, identity_context=identity_context)}"
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


def render_task_priorities_document() -> str:
    document_path = get_app_root() / "docs" / "plans" / "task_priorities.html"
    return document_path.read_text(encoding="utf-8")


def render_api_home() -> str:
    posts, threads, board_tags, _, moderation_state, _ = load_repository_state()
    return render_api_home_text(
        post_count=len(posts),
        thread_count=len(visible_threads(threads, moderation_state)),
        board_tags=board_tags,
    )


def render_api_list_index(board_tag: str | None) -> str:
    _, threads, board_tags, _, moderation_state, _ = load_repository_state()
    if board_tag and board_tag not in board_tags:
        return render_bad_request_text(f"unknown board_tag: {board_tag}")

    public_threads = visible_threads(threads, moderation_state, board_tag=board_tag)
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
) -> str:
    breadcrumb_items = [
        ("/", "board index"),
        ("/compose/thread" if command_name == "create_thread" else "/compose/reply", "signed compose"),
    ]
    content = load_template("compose.html").substitute(
        breadcrumb_html=render_breadcrumb(breadcrumb_items),
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
        body_value="",
        submit_label="Sign and preview" if dry_run else "Sign and submit",
    )
    return render_page(
        title=compose_heading,
        hero_kicker="Signed Posting",
        hero_title=compose_heading,
        hero_text=compose_text,
        content_html=content,
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

        if path == "/":
            body = render_board_index().encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path in {"/planning/task-priorities", "/planning/task-priorities/"}:
            body = render_task_priorities_document().encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/compose/thread":
            raw_board_tags = query_params.get("board_tags", [""])[0].strip() or query_params.get("board_tag", ["general"])[0].strip()
            board_tags = normalize_board_tags_text(raw_board_tags)
            body = render_compose_page(
                command_name="create_thread",
                endpoint_path="/api/create_thread",
                compose_heading="Compose a signed thread",
                compose_text="Generate or import a local OpenPGP key, sign a canonical thread payload in the browser, and submit the signed thread directly into repository storage.",
                dry_run=False,
                board_tags=board_tags,
                context_text=f"This page will open a new signed thread in {describe_board_tags(board_tags)}. The post ID and thread title are derived automatically from what you write.",
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

        if path == "/assets/vendor/openpgp.min.mjs":
            body = load_asset_text("vendor/openpgp.min.mjs").encode("utf-8")
            headers = [("Content-Type", "text/javascript; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/moderation/":
            limit = parse_limit_value(query_params.get("limit", [""])[0] if "limit" in query_params else None)
            before = query_params.get("before", [""])[0].strip() or None
            body = render_moderation_log_page(limit=limit, before=before).encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
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
