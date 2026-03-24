from __future__ import annotations

import json
import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

from forum_web.web import application


class IdentityHintApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def post(
        self,
        path: str,
        payload: dict[str, object],
        *,
        scheme: str = "http",
    ) -> tuple[str, dict[str, str], str]:
        body = json.dumps(payload).encode("utf-8")
        environ = {
            "PATH_INFO": path,
            "QUERY_STRING": "",
            "REQUEST_METHOD": "POST",
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": BytesIO(body),
            "wsgi.url_scheme": scheme,
        }
        response: dict[str, object] = {}

        def start_response(status: str, headers: list[tuple[str, str]], _exc_info=None) -> None:
            response["status"] = status
            response["headers"] = headers

        with mock.patch.dict(
            os.environ,
            {
                "FORUM_REPO_ROOT": str(self.repo_root),
                "FORUM_IDENTITY_HINT_SECRET": "test-secret",
            },
            clear=False,
        ):
            response_body = b"".join(application(environ, start_response)).decode("utf-8")
        return response["status"], dict(response["headers"]), response_body

    def test_set_identity_hint_sets_signed_cookie(self) -> None:
        status, headers, body = self.post(
            "/api/set_identity_hint",
            {"fingerprint": "ABCD1234EF567890"},
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Status: set", body)
        set_cookie = headers.get("Set-Cookie", "")
        self.assertIn("forum_identity_hint=", set_cookie)
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("SameSite=Lax", set_cookie)
        self.assertNotIn("Secure", set_cookie)

    def test_set_identity_hint_sets_secure_cookie_on_https(self) -> None:
        status, headers, _ = self.post(
            "/api/set_identity_hint",
            {"fingerprint": "ABCD1234EF567890"},
            scheme="https",
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Secure", headers.get("Set-Cookie", ""))

    def test_set_identity_hint_clears_cookie_when_fingerprint_missing(self) -> None:
        status, headers, body = self.post("/api/set_identity_hint", {})

        self.assertEqual(status, "200 OK")
        self.assertIn("Status: cleared", body)
        self.assertIn("Max-Age=0", headers.get("Set-Cookie", ""))


if __name__ == "__main__":
    unittest.main()
