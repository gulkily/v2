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
        self.assertIn('data-username-claim-cta', body)
        self.assertIn('/assets/username_claim_cta.js', body)
        self.assertNotIn("You can still claim one username for this profile.", body)

    def test_profile_page_hides_username_update_link_after_visible_claim(self) -> None:
        self.write_record(
            "records/profile-updates/profile-update-alpha.txt",
            f"""
            Record-ID: profile-update-alpha
            Action: set_display_name
            Source-Identity-ID: {IDENTITY_ID}
            Timestamp: 2026-03-18T00:00:00Z

            ClaimedName
            """,
        )

        status, _, body = self.get(f"/profiles/{PROFILE_SLUG}")

        self.assertEqual(status, "200 OK")
        self.assertNotIn(f'/profiles/{PROFILE_SLUG}/update', body)
        self.assertNotIn(">update username<", body)
        self.assertNotIn("You can still claim one username for this profile.", body)

    def test_profile_page_keeps_username_update_link_when_only_linked_peer_has_claim(self) -> None:
        other_identity_id = "openpgp:fedcba9876543210"
        other_slug = "openpgp-fedcba9876543210"
        self.write_record(
            f"records/identity/identity-{other_slug}.txt",
            f"""
            Post-ID: identity-{other_slug}
            Board-Tags: identity
            Subject: identity bootstrap
            Identity-ID: {other_identity_id}
            Signer-Fingerprint: FEDCBA9876543210
            Bootstrap-By-Post: other-root
            Bootstrap-By-Thread: other-root

            -----BEGIN PGP PUBLIC KEY BLOCK-----
            second
            -----END PGP PUBLIC KEY BLOCK-----
            """,
        )
        self.write_record(
            "records/profile-updates/profile-update-other.txt",
            f"""
            Record-ID: profile-update-other
            Action: set_display_name
            Source-Identity-ID: {other_identity_id}
            Timestamp: 2026-03-18T12:00:00Z

            SharedName
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-001.txt",
            f"""
            Record-ID: merge-request-001
            Action: request_merge
            Requester-Identity-ID: {IDENTITY_ID}
            Target-Identity-ID: {other_identity_id}
            Actor-Identity-ID: {IDENTITY_ID}
            Timestamp: 2026-03-18T12:10:00Z

            please merge
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-002.txt",
            f"""
            Record-ID: merge-request-002
            Action: approve_merge
            Requester-Identity-ID: {IDENTITY_ID}
            Target-Identity-ID: {other_identity_id}
            Actor-Identity-ID: {other_identity_id}
            Timestamp: 2026-03-18T12:11:00Z

            approved
            """,
        )

        status, _, body = self.get(f"/profiles/{PROFILE_SLUG}")

        self.assertEqual(status, "200 OK")
        self.assertIn(f'/profiles/{PROFILE_SLUG}/update', body)
        self.assertIn('data-username-claim-cta', body)
        self.assertNotIn("You can still claim one username for this profile.", body)

    def test_profile_page_keeps_shared_cta_mount_when_only_linked_peer_has_claim(self) -> None:
        other_identity_id = "openpgp:fedcba9876543210"
        other_slug = "openpgp-fedcba9876543210"
        self.write_record(
            f"records/identity/identity-{other_slug}.txt",
            f"""
            Post-ID: identity-{other_slug}
            Board-Tags: identity
            Subject: identity bootstrap
            Identity-ID: {other_identity_id}
            Signer-Fingerprint: FEDCBA9876543210
            Bootstrap-By-Post: other-root
            Bootstrap-By-Thread: other-root

            -----BEGIN PGP PUBLIC KEY BLOCK-----
            second
            -----END PGP PUBLIC KEY BLOCK-----
            """,
        )
        self.write_record(
            "records/profile-updates/profile-update-other.txt",
            f"""
            Record-ID: profile-update-other
            Action: set_display_name
            Source-Identity-ID: {other_identity_id}
            Timestamp: 2026-03-18T12:00:00Z

            SharedName
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-001.txt",
            f"""
            Record-ID: merge-request-001
            Action: request_merge
            Requester-Identity-ID: {IDENTITY_ID}
            Target-Identity-ID: {other_identity_id}
            Actor-Identity-ID: {IDENTITY_ID}
            Timestamp: 2026-03-18T12:10:00Z

            please merge
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-002.txt",
            f"""
            Record-ID: merge-request-002
            Action: approve_merge
            Requester-Identity-ID: {IDENTITY_ID}
            Target-Identity-ID: {other_identity_id}
            Actor-Identity-ID: {other_identity_id}
            Timestamp: 2026-03-18T12:11:00Z

            approved
            """,
        )

        status, _, body = self.get(f"/profiles/{PROFILE_SLUG}")

        self.assertEqual(status, "200 OK")
        self.assertIn('data-username-claim-cta', body)
        self.assertNotIn("You can still claim one username for this profile.", body)

    def test_profile_update_page_renders_identity_context(self) -> None:
        status, _, body = self.get(f"/profiles/{PROFILE_SLUG}/update")

        self.assertEqual(status, "200 OK")
        self.assertIn('class="site-header site-header--page"', body)
        self.assertIn("Update username", body)
        self.assertIn(DISPLAY_NAME, body)
        self.assertIn(IDENTITY_ID, body)
        self.assertIn("Choose a username:", body)
        self.assertIn('id="display-name-input" name="display_name" type="text" maxlength="80" value="" required', body)
        self.assertIn('id="profile-update-form"', body)
        self.assertIn('data-command="update_profile"', body)
        self.assertIn('data-dry-run="false"', body)
        self.assertIn('href="/account/key/"', body)
        self.assertIn('/assets/browser_signing.js', body)
        self.assertIn('id="private-key-input" class="technical-textarea" rows="10" spellcheck="false" wrap="off"', body)
        self.assertIn('id="public-key-output" class="technical-textarea key-display" rows="8" spellcheck="false" wrap="off" readonly', body)
        self.assertIn('id="payload-output"', body)
        self.assertIn('id="clear-pending-submission-button"', body)
        self.assertIn("Submit update", body)
        self.assertNotIn("Sign and submit", body)
        self.assertIn(">Technical details<", body)
        self.assertNotIn(">Advanced<", body)
        self.assertNotIn("Account setup", body)
        self.assertNotIn('data-username-claim-cta', body)
        self.assertNotIn("Profile Update", body)
        self.assertNotIn("Update your username", body)
        self.assertNotIn("Use the existing browser signing flow", body)
        self.assertNotIn('class="breadcrumb"', body)
        self.assertNotIn("Enter a new display name", body)
        self.assertNotIn(f'value="{DISPLAY_NAME}"', body)


if __name__ == "__main__":
    unittest.main()
