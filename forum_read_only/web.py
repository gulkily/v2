from __future__ import annotations

import html
import os
from pathlib import Path
from wsgiref.util import setup_testing_defaults

from forum_read_only.repository import group_threads, list_board_tags, load_posts
from forum_read_only.templates import load_asset_text, load_template, render_page


def get_repo_root() -> Path:
    env_root = os.environ.get("FORUM_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parent.parent


def render_home() -> str:
    posts = load_posts(get_repo_root() / "records" / "posts")
    threads = group_threads(posts)
    board_tags = list_board_tags(posts)

    stats_html = (
        '<div class="stat-grid">'
        f'<article class="stat-card"><span class="stat-number">{len(posts)}</span><span class="stat-label">posts loaded</span></article>'
        f'<article class="stat-card"><span class="stat-number">{len(threads)}</span><span class="stat-label">threads found</span></article>'
        f'<article class="stat-card"><span class="stat-number">{len(board_tags)}</span><span class="stat-label">board tags</span></article>'
        "</div>"
    )

    tag_items = "".join(
        f'<li class="tag-chip">{html.escape(tag)}</li>'
        for tag in board_tags
    )
    thread_items = "".join(
        "<li class=\"thread-chip\">"
        f"<strong>{html.escape(thread.root.post_id)}</strong>"
        f"<span>{html.escape(thread.root.subject or 'Untitled thread')}</span>"
        "</li>"
        for thread in threads
    )

    content = load_template("home.html").substitute(
        stats_html=stats_html,
        tags_html=tag_items,
        threads_html=thread_items,
    )
    return render_page(
        title="Forum Reader",
        hero_kicker="Read-Only Loop",
        hero_title="Canonical posts, rendered without a database",
        hero_text="This first shell reads the git-tracked post files directly and proves the sample repository can be loaded into deterministic thread and board-tag structures.",
        content_html=content,
    )


def render_not_found() -> str:
    return render_page(
        title="Not Found",
        hero_kicker="Missing route",
        hero_title="Nothing is published here yet",
        hero_text="This loop only exposes the minimal read-only shell so far. Board, thread, and permalink routes land in later stages of the same feature.",
        content_html='<section class="panel"><p>Available now: <a href="/">home</a> and <a href="/assets/site.css">site.css</a>.</p></section>',
    )


def application(environ, start_response):
    setup_testing_defaults(environ)
    path = environ.get("PATH_INFO", "/")

    try:
        if path == "/":
            body = render_home().encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/assets/site.css":
            body = load_asset_text("site.css").encode("utf-8")
            headers = [("Content-Type", "text/css; charset=utf-8")]
            start_response("200 OK", headers)
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
