from __future__ import annotations

import unittest
from io import BytesIO

from forum_cgi.wsgi_gateway import build_wsgi_environ_from_cgi, render_cgi_response


class WsgiGatewayTests(unittest.TestCase):
    def test_build_wsgi_environ_copies_request_shape_and_body(self) -> None:
        environ = build_wsgi_environ_from_cgi(
            env={
                "REQUEST_METHOD": "POST",
                "SCRIPT_NAME": "/index.php",
                "PATH_INFO": "/api/create_thread",
                "QUERY_STRING": "dry_run=0",
                "SERVER_NAME": "example.test",
                "SERVER_PORT": "443",
                "SERVER_PROTOCOL": "HTTP/1.1",
                "CONTENT_TYPE": "application/json",
                "CONTENT_LENGTH": "17",
                "REQUEST_SCHEME": "http",
                "HTTPS": "on",
                "HTTP_X_FORWARDED_PROTO": "https",
            },
            body_stream=BytesIO(b'{"hello":"world"}'),
        )

        self.assertEqual(environ["REQUEST_METHOD"], "POST")
        self.assertEqual(environ["SCRIPT_NAME"], "/index.php")
        self.assertEqual(environ["PATH_INFO"], "/api/create_thread")
        self.assertEqual(environ["QUERY_STRING"], "dry_run=0")
        self.assertEqual(environ["CONTENT_TYPE"], "application/json")
        self.assertEqual(environ["CONTENT_LENGTH"], "17")
        self.assertEqual(environ["wsgi.url_scheme"], "https")
        self.assertEqual(environ["HTTP_X_FORWARDED_PROTO"], "https")
        self.assertEqual(environ["wsgi.input"].read(), b'{"hello":"world"}')

    def test_render_cgi_response_serializes_status_headers_and_body(self) -> None:
        def application(environ, start_response):
            self.assertEqual(environ["PATH_INFO"], "/thread")
            self.assertEqual(environ["REQUEST_METHOD"], "GET")
            start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8"), ("X-Test", "1")])
            return [b"ready"]

        response = render_cgi_response(
            application,
            env={
                "REQUEST_METHOD": "GET",
                "PATH_INFO": "/thread",
                "QUERY_STRING": "",
            },
            body_stream=BytesIO(b""),
        ).decode("utf-8")

        self.assertTrue(response.startswith("Status: 200 OK\r\n"))
        self.assertIn("Content-Type: text/plain; charset=utf-8\r\n", response)
        self.assertIn("X-Test: 1\r\n", response)
        self.assertTrue(response.endswith("\r\nready"))

    def test_render_cgi_response_buffers_iterable_chunks_into_one_body(self) -> None:
        def application(environ, start_response):
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])

            def chunks():
                yield b"<p>loading</p>"
                yield b"<script>done()</script>"

            return chunks()

        response = render_cgi_response(
            application,
            env={
                "REQUEST_METHOD": "GET",
                "PATH_INFO": "/",
                "QUERY_STRING": "",
            },
            body_stream=BytesIO(b""),
        ).decode("utf-8")

        self.assertIn("<p>loading</p><script>done()</script>", response)


if __name__ == "__main__":
    unittest.main()
