from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

from forum_web.web import application


class SiteCssAssetTests(unittest.TestCase):
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

    def test_site_css_asset_exposes_preferred_color_scheme_support(self) -> None:
        status, headers, body = self.get("/assets/site.css")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers.get("Content-Type"), "text/css; charset=utf-8")
        self.assertIn("color-scheme: light dark;", body)
        self.assertIn("@media (prefers-color-scheme: dark)", body)
        self.assertIn("--surface-elevated:", body)
        self.assertIn("--surface-post-top:", body)

    def test_site_css_routes_shared_shell_through_theme_variables(self) -> None:
        _, _, body = self.get("/assets/site.css")

        self.assertIn(".site-header,", body)
        self.assertIn("background: var(--surface-elevated);", body)
        self.assertIn(".site-header-band {", body)
        self.assertIn("background: var(--surface-band);", body)
        self.assertIn(".site-username-claim {", body)
        self.assertIn("background: linear-gradient(135deg, var(--surface-claim-top), var(--surface-claim-bottom));", body)
        self.assertIn('.site-header-nav a[aria-current="page"] {', body)
        self.assertIn("border-color: var(--surface-chip-active-border);", body)
        self.assertIn("background: var(--surface-chip-active);", body)
        self.assertIn("color: var(--accent);", body)

    def test_site_css_routes_shared_components_through_theme_variables(self) -> None:
        _, _, body = self.get("/assets/site.css")

        self.assertIn(".thread-card {", body)
        self.assertIn("background: linear-gradient(180deg, var(--surface-card-top), var(--surface-card-bottom));", body)
        self.assertIn(".post-card {", body)
        self.assertIn("background: linear-gradient(180deg, var(--surface-post-top), var(--surface-post-bottom));", body)
        self.assertIn(".compose-card {", body)
        self.assertIn("background: var(--surface-compose-card);", body)
        self.assertIn(".board-index-thread-list {", body)
        self.assertIn("border-top: 1px solid var(--surface-board-divider);", body)


if __name__ == "__main__":
    unittest.main()
