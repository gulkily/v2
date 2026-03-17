from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.web import application


class MergeManagementApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.alpha = "openpgp:alpha"
        self.beta = "openpgp:beta"
        self.write_record(
            "records/identity/identity-openpgp-alpha.txt",
            f"""
            Post-ID: identity-openpgp-alpha
            Board-Tags: identity
            Subject: identity bootstrap
            Identity-ID: {self.alpha}
            Signer-Fingerprint: AAAAAAAAAAAAAAAA
            Bootstrap-By-Post: alpha-post
            Bootstrap-By-Thread: alpha-post

            -----BEGIN PGP PUBLIC KEY BLOCK-----
            alpha
            -----END PGP PUBLIC KEY BLOCK-----
            """,
        )
        self.write_record(
            "records/identity/identity-openpgp-beta.txt",
            f"""
            Post-ID: identity-openpgp-beta
            Board-Tags: identity
            Subject: identity bootstrap
            Identity-ID: {self.beta}
            Signer-Fingerprint: BBBBBBBBBBBBBBBB
            Bootstrap-By-Post: beta-post
            Bootstrap-By-Thread: beta-post

            -----BEGIN PGP PUBLIC KEY BLOCK-----
            beta
            -----END PGP PUBLIC KEY BLOCK-----
            """,
        )
        self.write_record(
            "records/profile-updates/profile-update-alpha.txt",
            f"""
            Record-ID: profile-update-alpha
            Action: set_display_name
            Source-Identity-ID: {self.alpha}
            Timestamp: 2026-03-17T21:00:00Z

            Ilya
            """,
        )
        self.write_record(
            "records/profile-updates/profile-update-beta.txt",
            f"""
            Record-ID: profile-update-beta
            Action: set_display_name
            Source-Identity-ID: {self.beta}
            Timestamp: 2026-03-17T21:10:00Z

            Ilya
            """,
        )

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

    def test_get_merge_management_lists_history_match_and_pending_request(self) -> None:
        self.write_record(
            "records/merge-requests/merge-request-001.txt",
            f"""
            Record-ID: merge-request-001
            Action: request_merge
            Requester-Identity-ID: {self.alpha}
            Target-Identity-ID: {self.beta}
            Actor-Identity-ID: {self.alpha}
            Timestamp: 2026-03-17T22:00:00Z

            please merge
            """,
        )

        status, _, body = self.get("/api/get_merge_management", f"identity_id={self.alpha}")

        self.assertEqual(status, "200 OK")
        self.assertIn("Historical-Match-Count: 1", body)
        self.assertIn("Outgoing-Request-Count: 1", body)
        self.assertIn(self.beta, body)
        self.assertIn("Ilya", body)

    def test_approved_merge_request_changes_profile_resolution(self) -> None:
        self.write_record(
            "records/merge-requests/merge-request-010.txt",
            f"""
            Record-ID: merge-request-010
            Action: request_merge
            Requester-Identity-ID: {self.alpha}
            Target-Identity-ID: {self.beta}
            Actor-Identity-ID: {self.alpha}
            Timestamp: 2026-03-17T22:00:00Z

            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-011.txt",
            f"""
            Record-ID: merge-request-011
            Action: approve_merge
            Requester-Identity-ID: {self.alpha}
            Target-Identity-ID: {self.beta}
            Actor-Identity-ID: {self.beta}
            Timestamp: 2026-03-17T22:05:00Z

            """,
        )

        status, _, body = self.get("/api/get_profile", f"identity_id={self.beta}")

        self.assertEqual(status, "200 OK")
        self.assertIn(f"Identity-ID: {self.alpha}", body)
        self.assertIn("Member-Identity-Count: 2", body)


if __name__ == "__main__":
    unittest.main()
