from __future__ import annotations

import html
import json
import os
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.util import setup_testing_defaults

from forum_cgi.posting import PostingError
from forum_cgi.service import submit_create_reply, submit_create_thread
from forum_cgi.text import render_error_body, render_submission_result
from forum_read_only.api_text import (
    render_api_home_text,
    render_bad_request_text,
    render_index_text,
    render_not_found_text,
    render_post_text,
    render_thread_text,
)
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
        reply_link_html=f'<p><a class="thread-chip" href="/compose/reply?thread_id={html.escape(thread.root.post_id)}&parent_id={html.escape(thread.root.post_id)}">compose a signed reply</a></p>',
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
        reply_link_html=f'<p><a class="thread-chip" href="/compose/reply?thread_id={html.escape(thread_target)}&parent_id={html.escape(post.post_id)}">reply to this post</a></p>',
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


def render_api_get_thread(thread_id: str | None) -> tuple[str, str]:
    if not thread_id:
        return "400 Bad Request", render_bad_request_text("missing required query parameter: thread_id")

    _, grouped_threads, _ = load_repository_state()
    thread = index_threads(grouped_threads).get(thread_id)
    if thread is None:
        return "404 Not Found", render_not_found_text("thread", thread_id)

    return "200 OK", render_thread_text(thread)


def render_api_get_post(post_id: str | None) -> tuple[str, str]:
    if not post_id:
        return "400 Bad Request", render_bad_request_text("missing required query parameter: post_id")

    posts, _, _ = load_repository_state()
    post = index_posts(posts).get(post_id)
    if post is None:
        return "404 Not Found", render_not_found_text("post", post_id)

    return "200 OK", render_post_text(post)


def render_compose_page(
    *,
    command_name: str,
    endpoint_path: str,
    compose_heading: str,
    compose_text: str,
    dry_run: bool,
    thread_id: str = "",
    parent_id: str = "",
) -> str:
    breadcrumb_items = [
        ("/", "board index"),
        ("/compose/thread" if command_name == "create_thread" else "/compose/reply", "signed compose"),
    ]
    content = load_template("compose.html").substitute(
        breadcrumb_html=render_breadcrumb(breadcrumb_items),
        compose_heading=html.escape(compose_heading),
        compose_text=html.escape(compose_text),
        command_name=html.escape(command_name),
        endpoint_path=html.escape(endpoint_path),
        dry_run_value="true" if dry_run else "false",
        post_id_value="",
        board_tags_value="general",
        subject_value="",
        thread_id_value=html.escape(thread_id),
        parent_id_value=html.escape(parent_id),
        body_value="",
        thread_id_readonly="readonly" if command_name == "create_thread" or thread_id else "",
        parent_id_readonly="readonly" if command_name == "create_thread" else "",
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
            status, body_text = render_api_create_thread(environ, default_dry_run=True)
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
            status, body_text = render_api_create_reply(environ, default_dry_run=True)
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

        if path == "/":
            body = render_board_index().encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/compose/thread":
            body = render_compose_page(
                command_name="create_thread",
                endpoint_path="/api/create_thread",
                compose_heading="Compose a signed thread",
                compose_text="Generate or import a local OpenPGP key, sign a canonical thread payload in the browser, and preview the signed submission before it is written.",
                dry_run=True,
            ).encode("utf-8")
            headers = [("Content-Type", "text/html; charset=utf-8")]
            start_response("200 OK", headers)
            return [body]

        if path == "/compose/reply":
            thread_id = query_params.get("thread_id", [""])[0].strip()
            parent_id = query_params.get("parent_id", [""])[0].strip()
            body = render_compose_page(
                command_name="create_reply",
                endpoint_path="/api/create_reply",
                compose_heading="Compose a signed reply",
                compose_text="Generate or import a local OpenPGP key, sign a canonical reply payload in the browser, and preview the signed submission before it is written.",
                dry_run=True,
                thread_id=thread_id,
                parent_id=parent_id,
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
