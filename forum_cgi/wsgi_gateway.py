from __future__ import annotations

import os
import sys
from io import BytesIO
from typing import BinaryIO, Callable, Iterable, Mapping


StartResponse = Callable[[str, list[tuple[str, str]]], None]
WsgiApplication = Callable[[dict[str, object], StartResponse], Iterable[bytes]]


def build_wsgi_environ_from_cgi(
    *,
    env: Mapping[str, str] | None = None,
    body_stream: BinaryIO | None = None,
) -> dict[str, object]:
    source_env = env or os.environ
    stream = body_stream or sys.stdin.buffer
    body = stream.read()
    environ: dict[str, object] = {
        "REQUEST_METHOD": source_env.get("REQUEST_METHOD", "GET"),
        "SCRIPT_NAME": source_env.get("SCRIPT_NAME", ""),
        "PATH_INFO": source_env.get("PATH_INFO", "/") or "/",
        "QUERY_STRING": source_env.get("QUERY_STRING", ""),
        "SERVER_NAME": source_env.get("SERVER_NAME", "localhost"),
        "SERVER_PORT": source_env.get("SERVER_PORT", "80"),
        "SERVER_PROTOCOL": source_env.get("SERVER_PROTOCOL", "HTTP/1.1"),
        "CONTENT_TYPE": source_env.get("CONTENT_TYPE", ""),
        "CONTENT_LENGTH": source_env.get("CONTENT_LENGTH", str(len(body))),
        "REMOTE_ADDR": source_env.get("REMOTE_ADDR", ""),
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": source_env.get("REQUEST_SCHEME", "http"),
        "wsgi.input": BytesIO(body),
        "wsgi.errors": sys.stderr,
        "wsgi.multithread": False,
        "wsgi.multiprocess": True,
        "wsgi.run_once": True,
    }
    for key, value in source_env.items():
        if key.startswith("HTTP_"):
            environ[key] = value
    if "HTTPS" in source_env and source_env["HTTPS"].lower() not in {"", "off", "0"}:
        environ["wsgi.url_scheme"] = "https"
    return environ


def render_cgi_response(
    application: WsgiApplication,
    *,
    env: Mapping[str, str] | None = None,
    body_stream: BinaryIO | None = None,
) -> bytes:
    environ = build_wsgi_environ_from_cgi(env=env, body_stream=body_stream)
    captured_status = "200 OK"
    captured_headers: list[tuple[str, str]] = []

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        nonlocal captured_status, captured_headers
        captured_status = status
        captured_headers = headers

    chunks = application(environ, start_response)
    try:
        body = b"".join(chunks)
    finally:
        close = getattr(chunks, "close", None)
        if callable(close):
            close()
    lines = [f"Status: {captured_status}"]
    lines.extend(f"{name}: {value}" for name, value in captured_headers)
    lines.append("")
    return "\r\n".join(lines).encode("utf-8") + b"\r\n" + body
