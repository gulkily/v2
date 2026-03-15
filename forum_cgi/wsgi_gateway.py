from __future__ import annotations

import os
import sys
from io import BytesIO
from typing import Callable, Iterable


StartResponse = Callable[[str, list[tuple[str, str]]], None]
WsgiApplication = Callable[[dict[str, object], StartResponse], Iterable[bytes]]


def build_wsgi_environ_from_cgi() -> dict[str, object]:
    body = sys.stdin.buffer.read()
    environ: dict[str, object] = {
        "REQUEST_METHOD": os.environ.get("REQUEST_METHOD", "GET"),
        "SCRIPT_NAME": os.environ.get("SCRIPT_NAME", ""),
        "PATH_INFO": os.environ.get("PATH_INFO", "/") or "/",
        "QUERY_STRING": os.environ.get("QUERY_STRING", ""),
        "SERVER_NAME": os.environ.get("SERVER_NAME", "localhost"),
        "SERVER_PORT": os.environ.get("SERVER_PORT", "80"),
        "SERVER_PROTOCOL": os.environ.get("SERVER_PROTOCOL", "HTTP/1.1"),
        "CONTENT_TYPE": os.environ.get("CONTENT_TYPE", ""),
        "CONTENT_LENGTH": os.environ.get("CONTENT_LENGTH", str(len(body))),
        "REMOTE_ADDR": os.environ.get("REMOTE_ADDR", ""),
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": os.environ.get("REQUEST_SCHEME", "http"),
        "wsgi.input": BytesIO(body),
        "wsgi.errors": sys.stderr,
        "wsgi.multithread": False,
        "wsgi.multiprocess": True,
        "wsgi.run_once": True,
    }
    for key, value in os.environ.items():
        if key.startswith("HTTP_"):
            environ[key] = value
    if "HTTPS" in os.environ and os.environ["HTTPS"].lower() not in {"", "off", "0"}:
        environ["wsgi.url_scheme"] = "https"
    return environ


def render_cgi_response(application: WsgiApplication) -> bytes:
    environ = build_wsgi_environ_from_cgi()
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

