from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.web import application


class MyProfileEmptyStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_record(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")

    def get(self, path: str, query_string: str = "") -> tuple[str, dict[str, str], str]:
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

        with mock.patch.dict(os.environ, {"FORUM_REPO_ROOT": str(self.repo_root)}):
            body = b"".join(application(environ, start_response)).decode("utf-8")

        return response["status"], dict(response["headers"]), body

    def test_self_marked_profile_without_visible_records_renders_empty_state(self) -> None:
        status, _, body = self.get("/profiles/openpgp-alpha", "self=1")

        self.assertEqual(status, "200 OK")
        self.assertIn('data-profile-empty-state', body)
        self.assertIn("Your profile is ready to start", body)
        self.assertIn("publish your first signed post", body)
        self.assertIn("/compose/thread", body)
        self.assertNotIn("This record could not be located", body)

    def test_unknown_profile_without_self_marker_still_returns_missing_resource(self) -> None:
        status, _, body = self.get("/profiles/openpgp-alpha")

        self.assertEqual(status, "404 Not Found")
        self.assertIn("This record could not be located", body)
        self.assertNotIn('data-profile-empty-state', body)

    def test_self_marked_published_profile_still_renders_normal_profile_page(self) -> None:
        self.write_record(
            "records/identity/identity-openpgp-alpha.txt",
            """
            Post-ID: identity-openpgp-alpha
            Board-Tags: identity
            Subject: identity bootstrap
            Identity-ID: openpgp:alpha
            Signer-Fingerprint: AAAAAAAAAAAAAAAA
            Bootstrap-By-Post: root-alpha
            Bootstrap-By-Thread: root-alpha

            -----BEGIN PGP PUBLIC KEY BLOCK-----
            alpha
            -----END PGP PUBLIC KEY BLOCK-----
            """,
        )

        status, _, body = self.get("/profiles/openpgp-alpha", "self=1")

        self.assertEqual(status, "200 OK")
        self.assertIn(">Signed posts<", body)
        self.assertIn(">Technical details<", body)
        self.assertNotIn('data-profile-empty-state', body)
        self.assertNotIn("Your profile is ready to start", body)


if __name__ == "__main__":
    unittest.main()
