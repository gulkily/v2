from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_read_only.web import application


IDENTITY_ID = "openpgp:0123456789abcdef"
PROFILE_SLUG = "openpgp-0123456789abcdef"
DISPLAY_NAME = "0123456789ABCDEF"


class ProfileUpdatePageTests(unittest.TestCase):
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
            Signer-Fingerprint: {DISPLAY_NAME}
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

        return (
            response["status"],
            dict(response["headers"]),
            body,
        )

    def test_profile_page_links_to_username_update_flow(self) -> None:
        status, _, body = self.get(f"/profiles/{PROFILE_SLUG}")

        self.assertEqual(status, "200 OK")
        self.assertIn(f'/profiles/{PROFILE_SLUG}/update', body)
        self.assertIn("update username", body)

    def test_profile_update_page_renders_identity_context(self) -> None:
        status, _, body = self.get(f"/profiles/{PROFILE_SLUG}/update")

        self.assertEqual(status, "200 OK")
        self.assertIn("Update username", body)
        self.assertIn(DISPLAY_NAME, body)
        self.assertIn(IDENTITY_ID, body)
        self.assertIn('id="profile-update-form"', body)
        self.assertIn('data-command="update_profile"', body)
        self.assertIn('data-dry-run="true"', body)
        self.assertIn('/assets/browser_signing.js', body)
        self.assertIn('id="private-key-input"', body)
        self.assertIn('id="payload-output"', body)
        self.assertIn("Sign and preview", body)


if __name__ == "__main__":
    unittest.main()
