from __future__ import annotations

import html
import os
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.util import setup_testing_defaults

from forum_read_only.api_text import render_api_home_text
from forum_read_only.api_text import render_bad_request_text, render_index_text
from forum_read_only.repository import (
    group_threads,
    index_posts,
    index_threads,
    list_board_tags,
    list_threads_by_board,
    load_posts,
)
from forum_read_only.templates import load_asset_text, load_template, render_page


def get_repo_root() -> Path:
    env_root = os.environ.get("FORUM_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parent.parent


def load_repository_state():
    posts = load_posts(get_repo_root() / "records" / "posts")
    threads = group_threads(posts)
    board_tags = list_board_tags(posts)
    return posts, threads, board_tags


def render_board_index() -> str:
    posts, threads, board_tags = load_repository_state()
    board_sections = list_threads_by_board(threads)

    stats_html = (
        '<div class="stat-grid">'
        f'<article class="stat-card"><span class="stat-number">{len(posts)}</span><span class="stat-label">posts loaded</span></article>'
        f'<article class="stat-card"><span class="stat-number">{len(threads)}</span><span class="stat-label">threads found</span></article>'
        f'<article class="stat-card"><span class="stat-number">{len(board_tags)}</span><span class="stat-label">board tags</span></article>'
        "</div>"
    )

    tag_items = "".join(f'<a class="tag-chip" href="#board-{html.escape(tag)}">{html.escape(tag)}</a>' for tag in board_tags)
    board_sections_html = "".join(render_board_section(tag, section_threads) for tag, section_threads in board_sections)

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


def render_board_section(tag: str, threads) -> str:
    thread_cards = "".join(
        "<article class=\"thread-card\">"
        f"<p class=\"thread-id\">{html.escape(thread.root.post_id)}</p>"
        f"<h3><a href=\"/threads/{html.escape(thread.root.post_id)}\">{html.escape(thread.root.subject or 'Untitled thread')}</a></h3>"
        f"<p>{html.escape(first_line(thread.root.body))}</p>"
        f"<p class=\"thread-meta\">{len(thread.replies)} repl{'y' if len(thread.replies) == 1 else 'ies'}</p>"
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
    posts, grouped_threads, _ = load_repository_state()
    threads = index_threads(grouped_threads)
    thread = threads.get(thread_id)
    if thread is None:
        raise LookupError(f"unknown thread: {thread_id}")

    content = load_template("thread.html").substitute(
        breadcrumb_html=render_breadcrumb(
            [
                ('/', 'board index'),
                ('/threads/' + thread.root.post_id, thread.root.subject or thread.root.post_id),
            ]
        ),
        thread_heading=html.escape(thread.root.subject or thread.root.post_id),
        thread_meta=f"{len(thread.replies)} repl{'y' if len(thread.replies) == 1 else 'ies'} in this thread.",
        root_post_html=render_post_card(thread.root, root_thread_id=thread.root.post_id),
        replies_html="".join(render_post_card(reply, root_thread_id=thread.root.post_id) for reply in thread.replies),
    )
    return render_page(
        title=thread.root.subject or thread.root.post_id,
        hero_kicker="Thread View",
        hero_title=thread.root.subject or thread.root.post_id,
        hero_text="The thread page is rendered directly from canonical post files without a database, using deterministic reply ordering from the repository state.",
        content_html=content,
    )


def render_post(post_id: str) -> str:
    posts, _, _ = load_repository_state()
    post = index_posts(posts).get(post_id)
    if post is None:
        raise LookupError(f"unknown post: {post_id}")

    thread_target = post.root_thread_id
    heading = post.subject or post.post_id
    content = load_template("post.html").substitute(
        breadcrumb_html=render_breadcrumb(
            [
                ('/', 'board index'),
                ('/threads/' + thread_target, thread_target),
                ('/posts/' + post.post_id, post.post_id),
            ]
        ),
        post_heading=html.escape(heading),
        post_card_html=render_post_card(post, root_thread_id=thread_target),
    )
    return render_page(
        title=heading,
        hero_kicker="Post Permalink",
        hero_title=heading,
        hero_text="This permalink shows one canonical post in isolation while preserving links back to the thread and board index.",
        content_html=content,
    )


def render_post_card(post, *, root_thread_id: str) -> str:
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

    return (
        '<article class="post-card">'
        '<div class="post-meta-row">'
        f'<p class="post-id">{html.escape(post.post_id)}</p>'
        f'<p class="post-tags">{board_tags}</p>'
        "</div>"
        f"{subject_html}"
        f"{relation_html}"
        f'<div class="post-body">{render_body_html(post.body)}</div>'
        f'<p class="post-link"><a href="/posts/{html.escape(post.post_id)}">permalink</a></p>'
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


def render_api_home() -> str:
    posts, threads, board_tags = load_repository_state()
    return render_api_home_text(
        post_count=len(posts),
        thread_count=len(threads),
        board_tags=board_tags,
    )


def render_api_list_index(board_tag: str | None) -> str:
    _, threads, board_tags = load_repository_state()
    if board_tag and board_tag not in board_tags:
        return render_bad_request_text(f"unknown board_tag: {board_tag}")

    if board_tag:
        threads = [
            thread
            for thread in threads
            if board_tag in thread.root.board_tags
        ]

    return render_index_text(threads, board_tag=board_tag)


def application(environ, start_response):
    setup_testing_defaults(environ)
    path = environ.get("PATH_INFO", "/")
    query_params = parse_qs(environ.get("QUERY_STRING", ""))

    try:
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

        if path == "/":
            body = render_board_index().encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/assets/site.css":
            body = load_asset_text("site.css").encode("utf-8")
            headers = [("Content-Type", "text/css; charset=utf-8")]
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

        body = render_not_found().encode("utf-8")
        headers = [("Content-Type", "text/html; charset=utf-8")]
        start_response("404 Not Found", headers)
        return [body]
    except Exception as exc:  # pragma: no cover - manual smoke checks cover this path
        body = (
            "<!doctype html><title>Server Error</title>"
            f"<pre>{html.escape(str(exc))}</pre>"
        ).encode("utf-8")
        headers = [("Content-Type", "text/html; charset=utf-8")]
        start_response("500 Internal Server Error", headers)
        return [body]
