from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

from forum_web.web import application


class ComposeThreadPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def get(self, path: str, query_string: str = "") -> tuple[str, dict[str, str], str]:
        return self.get_with_env(path, query_string=query_string)

    def get_with_env(self, path: str, *, query_string: str = "", extra_env: dict[str, str] | None = None) -> tuple[str, dict[str, str], str]:
        environ = {
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
            "REQUEST_METHOD": "GET",
            "CONTENT_LENGTH": "0",
            "wsgi.input": BytesIO(b""),
        }
        response: dict[str, object] = {}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = status
            response["headers"] = headers

        env = {"FORUM_REPO_ROOT": str(self.repo_root)}
        if extra_env:
            env.update(extra_env)

        with mock.patch.dict(os.environ, env):
            body = b"".join(application(environ, start_response)).decode("utf-8")

        return (
            response["status"],
            dict(response["headers"]),
            body,
        )

    def test_compose_thread_page_renders_shared_draft_status_hook(self) -> None:
        status, _, body = self.get("/compose/thread")

        self.assertEqual(status, "200 OK")
        self.assertIn('class="site-header site-header--page"', body)
        self.assertIn('class="site-footer"', body)
        self.assertIn("Compose a signed thread", body)
        self.assertIn('id="signed-post-form"', body)
        self.assertIn('id="draft-status"', body)
        self.assertIn('id="remove-unsupported-button"', body)
        self.assertIn('id="compose-normalization-status"', body)
        self.assertIn('data-command="create_thread"', body)
        self.assertIn('data-thread-type=""', body)
        self.assertNotIn("Only the body is typed manually", body)
        self.assertNotIn(">Technical details<", body)
        self.assertIn(">Advanced<", body)

    def test_compose_thread_page_exposes_pow_settings_when_enabled(self) -> None:
        status, _, body = self.get_with_env(
            "/compose/thread",
            extra_env={
                "FORUM_ENABLE_FIRST_POST_POW": "1",
                "FORUM_FIRST_POST_POW_DIFFICULTY": "9",
            },
        )

        self.assertEqual(status, "200 OK")
        self.assertIn('data-pow-enabled="true"', body)
        self.assertIn('data-pow-difficulty="9"', body)


if __name__ == "__main__":
    unittest.main()
