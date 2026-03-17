from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.web import application


IDENTITY_ID = "openpgp:0123456789abcdef"
OTHER_IDENTITY_ID = "openpgp:fedcba9876543210"
PROFILE_SLUG = "openpgp-0123456789abcdef"


class MergeManagementPageTests(unittest.TestCase):
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
            Signer-Fingerprint: 0123456789ABCDEF
            Bootstrap-By-Post: root-identity
            Bootstrap-By-Thread: root-identity

            -----BEGIN PGP PUBLIC KEY BLOCK-----
            example
            -----END PGP PUBLIC KEY BLOCK-----
            """,
        )
        self.write_record(
            "records/identity/identity-openpgp-fedcba9876543210.txt",
            f"""
            Post-ID: identity-openpgp-fedcba9876543210
            Board-Tags: identity
            Subject: identity bootstrap
            Identity-ID: {OTHER_IDENTITY_ID}
            Signer-Fingerprint: FEDCBA9876543210
            Bootstrap-By-Post: other-identity
            Bootstrap-By-Thread: other-identity

            -----BEGIN PGP PUBLIC KEY BLOCK-----
            example
            -----END PGP PUBLIC KEY BLOCK-----
            """,
        )
        self.write_record(
            "records/profile-updates/profile-update-a.txt",
            f"""
            Record-ID: profile-update-a
            Action: set_display_name
            Source-Identity-ID: {IDENTITY_ID}
            Timestamp: 2026-03-17T20:00:00Z

            Ilya
            """,
        )
        self.write_record(
            "records/profile-updates/profile-update-b.txt",
            f"""
            Record-ID: profile-update-b
            Action: set_display_name
            Source-Identity-ID: {OTHER_IDENTITY_ID}
            Timestamp: 2026-03-17T20:10:00Z

            Ilya
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-001.txt",
            f"""
            Record-ID: merge-request-001
            Action: request_merge
            Requester-Identity-ID: {OTHER_IDENTITY_ID}
            Target-Identity-ID: {IDENTITY_ID}
            Actor-Identity-ID: {OTHER_IDENTITY_ID}
            Timestamp: 2026-03-17T21:00:00Z

            please merge
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

    def test_profile_page_links_to_merge_management(self) -> None:
        status, _, body = self.get(f"/profiles/{PROFILE_SLUG}")

        self.assertEqual(status, "200 OK")
        self.assertIn(f"/profiles/{PROFILE_SLUG}/merge", body)
        self.assertIn("manage merges", body)

    def test_merge_management_page_renders_matches_and_incoming_actions(self) -> None:
        status, _, body = self.get(f"/profiles/{PROFILE_SLUG}/merge")

        self.assertEqual(status, "200 OK")
        self.assertIn("Manage identity merges", body)
        self.assertIn(OTHER_IDENTITY_ID, body)
        self.assertIn("Last activity", body)
        self.assertIn("Visible posts", body)
        self.assertIn("No visible signed posts yet", body)
        self.assertIn("request merge", body)
        self.assertIn("approve", body)
        self.assertIn("dismiss", body)
        self.assertIn("moderator approve", body)

    def test_merge_action_page_renders_signing_flow(self) -> None:
        status, _, body = self.get(
            f"/profiles/{PROFILE_SLUG}/merge/action",
            f"action=approve_merge&requester_identity_id={OTHER_IDENTITY_ID}&target_identity_id={IDENTITY_ID}",
        )

        self.assertEqual(status, "200 OK")
        self.assertIn('id="merge-request-app"', body)
        self.assertIn('data-action="approve_merge"', body)
        self.assertIn(f'data-requester-identity-id="{OTHER_IDENTITY_ID}"', body)
        self.assertIn(f'data-target-identity-id="{IDENTITY_ID}"', body)
        self.assertIn("/assets/merge_request_signing.js", body)


if __name__ == "__main__":
    unittest.main()
