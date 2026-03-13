from __future__ import annotations

import html
import os
from pathlib import Path
from wsgiref.util import setup_testing_defaults

from forum_read_only.repository import group_threads, list_board_tags, list_threads_by_board, load_posts
from forum_read_only.templates import load_asset_text, load_template, render_page


def get_repo_root() -> Path:
    env_root = os.environ.get("FORUM_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parent.parent


def render_board_index() -> str:
    posts = load_posts(get_repo_root() / "records" / "posts")
    threads = group_threads(posts)
    board_tags = list_board_tags(posts)
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
        f"<p>{html.escape(thread.root.body.splitlines()[0])}</p>"
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


def render_not_found() -> str:
    return render_page(
        title="Not Found",
        hero_kicker="Missing route",
        hero_title="Nothing is published here yet",
        hero_text="This loop is publishing the board index first. Thread and permalink routes land in later stages of the same feature.",
        content_html='<section class="panel"><p>Available now: <a href="/">board index</a> and <a href="/assets/site.css">site.css</a>.</p></section>',
    )


def application(environ, start_response):
    setup_testing_defaults(environ)
    path = environ.get("PATH_INFO", "/")

    try:
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
