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

    def get_bytes(
        self,
        path: str,
        *,
        query_string: str = "",
        extra_env: dict[str, str] | None = None,
    ) -> tuple[str, dict[str, str], bytes]:
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
            body = b"".join(application(environ, start_response))

        return (
            response["status"],
            dict(response["headers"]),
            body,
        )

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
        self.assertNotIn("Signed Posting", body)
        self.assertNotIn('class="breadcrumb"', body)
        self.assertIn('id="signed-post-form"', body)
        self.assertIn(">Submit post<", body)
        self.assertNotIn("Sign and submit", body)
        self.assertIn('id="draft-status"', body)
        self.assertIn('id="clear-pending-submission-button"', body)
        self.assertIn('id="remove-unsupported-button"', body)
        self.assertIn('id="compose-normalization-status"', body)
        self.assertIn('id="public-key-output" class="technical-textarea key-display profile-public-key-textarea"', body)
        self.assertIn('id="private-key-input" class="technical-textarea" rows="10" spellcheck="false" wrap="off"', body)
        self.assertIn('id="public-key-output" class="technical-textarea key-display profile-public-key-textarea" rows="8" spellcheck="false" wrap="off" readonly', body)
        self.assertIn('data-command="create_thread"', body)
        self.assertIn('data-thread-type=""', body)
        self.assertIn('data-unsigned-fallback-enabled="', body)
        self.assertIn('data-username-claim-cta', body)
        self.assertIn('/assets/username_claim_cta.js', body)
        self.assertIn("Choose your username", body)
        self.assertIn("Requirements and limitations", body)
        self.assertIn("ASCII-only canonical text records", body)
        self.assertIn("reduces Unicode obfuscation risks", body)
        self.assertIn("normalize common punctuation to ASCII", body)
        self.assertNotIn("<h2>Compose a signed thread</h2>", body)
        self.assertNotIn(">Signed Post<", body)
        self.assertNotIn("Only the body is typed manually", body)
        self.assertIn(">Technical details<", body)
        self.assertNotIn(">Advanced<", body)

        textarea_index = body.index('id="body-input"')
        draft_status_index = body.index('id="draft-status"')
        requirements_index = body.index("Requirements and limitations")

        self.assertLess(textarea_index, draft_status_index)
        self.assertLess(draft_status_index, requirements_index)

    def test_openpgp_loader_asset_is_served(self) -> None:
        status, headers, body = self.get("/assets/openpgp_loader.js")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers.get("Content-Type"), "text/javascript; charset=utf-8")
        self.assertIn("async function loadOpenPgp()", body)

    def test_copy_field_asset_is_served(self) -> None:
        status, headers, body = self.get("/assets/copy_field.js")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers.get("Content-Type"), "text/javascript; charset=utf-8")
        self.assertIn('document.addEventListener("click"', body)

    def test_site_css_declares_dark_mode_theme_tokens(self) -> None:
        status, headers, body = self.get("/assets/site.css")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers.get("Content-Type"), "text/css; charset=utf-8")
        self.assertIn("color-scheme: light dark;", body)
        self.assertIn("@media (prefers-color-scheme: dark)", body)
        self.assertIn("--surface-elevated:", body)

    def test_favicon_svg_asset_is_served(self) -> None:
        status, headers, body = self.get("/assets/favicon.svg")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers.get("Content-Type"), "image/svg+xml; charset=utf-8")
        self.assertIn("<svg", body)

    def test_favicon_ico_is_served_for_older_browser_requests(self) -> None:
        status, headers, body = self.get_bytes("/favicon.ico")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers.get("Content-Type"), "image/x-icon")
        self.assertTrue(body.startswith(b"\x00\x00\x01\x00"))
        self.assertGreater(len(body), 100)

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

    def test_compose_thread_page_exposes_unsigned_fallback_flag_when_enabled(self) -> None:
        status, _, body = self.get_with_env(
            "/compose/thread",
            extra_env={"FORUM_ENABLE_UNSIGNED_POST_FALLBACK": "1"},
        )

        self.assertEqual(status, "200 OK")
        self.assertIn('data-unsigned-fallback-enabled="true"', body)

    def test_compose_thread_page_source_uses_multiline_shared_shell_blocks(self) -> None:
        status, _, body = self.get("/compose/thread")

        self.assertEqual(status, "200 OK")
        self.assertIn('<header class="site-header site-header--page">\n', body)
        self.assertIn('<nav class="site-header-nav" aria-label="Primary">\n', body)
        self.assertIn('</section>\n    <script>\n', body)
        self.assertIn('</nav>\n', body)
        self.assertIn('</header>\n    <main class="content-shell">', body)
        self.assertIn(
            '<script type="module" src="/assets/profile_nav.js"></script>\n'
            '  <script type="module" src="/assets/username_claim_cta.js"></script>\n'
            '  <script type="module" src="/assets/copy_field.js"></script>\n'
            '  <script type="module" src="/assets/browser_signing.js"></script>',
            body,
        )


if __name__ == "__main__":
    unittest.main()
