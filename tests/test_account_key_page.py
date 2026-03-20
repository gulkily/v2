from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

from forum_web.web import application


class AccountKeyPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def get(self, path: str) -> tuple[str, dict[str, str], str]:
        environ = {
            "PATH_INFO": path,
            "QUERY_STRING": "",
            "REQUEST_METHOD": "GET",
            "CONTENT_LENGTH": "0",
            "wsgi.input": BytesIO(b""),
        }
        response: dict[str, object] = {}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = status
            response["headers"] = headers

        with mock.patch.dict(os.environ, {"FORUM_REPO_ROOT": str(self.repo_root)}):
            body = b"".join(application(environ, start_response)).decode("utf-8")

        return response["status"], dict(response["headers"]), body

    def test_account_key_page_renders_browser_key_viewer(self) -> None:
        status, headers, body = self.get("/account/key/")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("Key material", body)
        self.assertIn("browser-stored signing key available on this device", body)
        self.assertIn('id="key-material-status"', body)
        self.assertIn('id="generate-key-button" type="button">Generate New Key</button>', body)
        self.assertIn('id="import-key-button" type="button">Import Key</button>', body)
        self.assertIn('id="key-private-key-output" class="technical-textarea" rows="10" spellcheck="false" wrap="off"></textarea>', body)
        self.assertIn('id="key-public-key-output" class="technical-textarea key-display" rows="8" spellcheck="false" wrap="off" readonly', body)
        self.assertIn('/assets/profile_key_viewer.js', body)
        self.assertIn('/assets/account_key_actions.js', body)


if __name__ == "__main__":
    unittest.main()
