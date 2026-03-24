from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.identity_hint import build_identity_hint_cookie_value
from forum_web.web import application


IDENTITY_FINGERPRINT = "0123456789ABCDEF0123456789ABCDEF01234567"
IDENTITY_ID = f"openpgp:{IDENTITY_FINGERPRINT.lower()}"
PROFILE_SLUG = f"openpgp-{IDENTITY_FINGERPRINT.lower()}"


class AccountSetupInitialRenderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.write_record(
            f"records/identity/identity-{PROFILE_SLUG}.txt",
            f"""
            Post-ID: identity-{PROFILE_SLUG}
            Board-Tags: identity
            Subject: identity bootstrap
            Identity-ID: {IDENTITY_ID}
            Signer-Fingerprint: {IDENTITY_FINGERPRINT}
            Bootstrap-By-Post: root-identity
            Bootstrap-By-Thread: root-identity

            -----BEGIN PGP PUBLIC KEY BLOCK-----
            example
            -----END PGP PUBLIC KEY BLOCK-----
            """,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_record(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")

    def get(self, path: str, *, cookie: str | None = None) -> tuple[str, dict[str, str], str]:
        environ = {
            "PATH_INFO": path,
            "QUERY_STRING": "",
            "REQUEST_METHOD": "GET",
            "CONTENT_LENGTH": "0",
            "wsgi.input": BytesIO(b""),
        }
        if cookie is not None:
            environ["HTTP_COOKIE"] = cookie
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
            body = b"".join(application(environ, start_response)).decode("utf-8")

        return response["status"], dict(response["headers"]), body

    def identity_hint_cookie(self, *, raw_value: str | None = None) -> str:
        value = raw_value or build_identity_hint_cookie_value(
            IDENTITY_FINGERPRINT,
            secret="test-secret",
            max_age=3600,
        )
        return f"forum_identity_hint={value}"

    def test_board_index_initial_html_renders_visible_banner_for_valid_hint_cookie(self) -> None:
        status, _, body = self.get("/", cookie=self.identity_hint_cookie())

        self.assertEqual(status, "200 OK")
        self.assertIn('<section class="site-username-claim panel" data-username-claim-cta>', body)
        self.assertIn(f'"updateHref": "/profiles/{PROFILE_SLUG}/update"', body)
        self.assertIn("forum_username_claim_cta", body)
        self.assertIn('/assets/username_claim_cta.js', body)
        self.assertIn("Account setup", body)

    def test_compose_thread_initial_html_renders_visible_banner_for_valid_hint_cookie(self) -> None:
        status, _, body = self.get("/compose/thread", cookie=self.identity_hint_cookie())

        self.assertEqual(status, "200 OK")
        self.assertIn('<section class="site-username-claim panel" data-username-claim-cta>', body)
        self.assertIn(f'"updateHref": "/profiles/{PROFILE_SLUG}/update"', body)
        self.assertIn('/assets/username_claim_cta.js', body)

    def test_invalid_hint_cookie_fails_closed_to_hidden_banner(self) -> None:
        invalid_cookie = self.identity_hint_cookie(raw_value="v1.bad.9999999999.invalid")
        status, _, body = self.get("/", cookie=invalid_cookie)

        self.assertEqual(status, "200 OK")
        self.assertIn('"visible": false', body)
        self.assertIn('data-username-claim-link href=""', body)

    def test_expired_hint_cookie_fails_closed_to_hidden_banner(self) -> None:
        expired_value = build_identity_hint_cookie_value(
            IDENTITY_FINGERPRINT,
            secret="test-secret",
            now=1,
            max_age=1,
        )
        status, _, body = self.get("/", cookie=self.identity_hint_cookie(raw_value=expired_value))

        self.assertEqual(status, "200 OK")
        self.assertIn('"visible": false', body)
        self.assertIn('data-username-claim-link href=""', body)


if __name__ == "__main__":
    unittest.main()
