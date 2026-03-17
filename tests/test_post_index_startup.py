from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

from forum_web import web


class PostIndexStartupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        (self.repo_root / "records" / "posts").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "records" / "posts" / "root-001.txt").write_text(
            "Post-ID: root-001\nBoard-Tags: general\nSubject: Hello\n\nBody.\n",
            encoding="ascii",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def request(self, path: str) -> tuple[str, dict[str, str], str]:
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

        with mock.patch.dict(os.environ, {"FORUM_REPO_ROOT": str(self.repo_root)}, clear=False):
            body = b"".join(web.application(environ, start_response)).decode("utf-8")
        return response["status"], dict(response["headers"]), body

    def test_application_eagerly_initializes_post_index_once_per_repo_root(self) -> None:
        web._INDEX_STARTUP_READY_ROOTS.clear()

        with mock.patch("forum_web.web.ensure_post_index_current") as mock_ensure:
            mock_ensure.return_value = mock.Mock()

            first_status, _, _ = self.request("/instance/")
            second_status, _, _ = self.request("/instance/")

        self.assertEqual(first_status, "200 OK")
        self.assertEqual(second_status, "200 OK")
        self.assertEqual(mock_ensure.call_count, 1)
        self.assertEqual(mock_ensure.call_args.args[0], self.repo_root.resolve())


if __name__ == "__main__":
    unittest.main()
