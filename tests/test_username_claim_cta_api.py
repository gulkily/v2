from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.web import application


class UsernameClaimCtaApiTests(unittest.TestCase):
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

    def test_get_username_claim_cta_requires_identity_id(self) -> None:
        status, _, body = self.get("/api/get_username_claim_cta")

        self.assertEqual(status, "400 Bad Request")
        self.assertIn("missing required query parameter: identity_id", body)

    def test_get_username_claim_cta_returns_eligible_state_for_unclaimed_identity(self) -> None:
        status, _, body = self.get("/api/get_username_claim_cta", f"identity_id={self.alpha}")

        self.assertEqual(status, "200 OK")
        self.assertIn("Command: get_username_claim_cta", body)
        self.assertIn(f"Identity-ID: {self.alpha}", body)
        self.assertIn("Can-Claim-Username: yes", body)
        self.assertIn("Update-Href: /profiles/openpgp-alpha/update", body)

    def test_get_username_claim_cta_returns_ineligible_state_after_claim(self) -> None:
        self.write_record(
            "records/profile-updates/profile-update-alpha.txt",
            f"""
            Record-ID: profile-update-alpha
            Action: set_display_name
            Source-Identity-ID: {self.alpha}
            Timestamp: 2026-03-18T00:00:00Z

            ClaimedAlpha
            """,
        )

        status, _, body = self.get("/api/get_username_claim_cta", f"identity_id={self.alpha}")

        self.assertEqual(status, "200 OK")
        self.assertIn(f"Identity-ID: {self.alpha}", body)
        self.assertIn("Can-Claim-Username: no", body)
        self.assertNotIn("Update-Href:", body)

    def test_get_username_claim_cta_keeps_unspent_identity_eligible_when_linked_peer_has_claim(self) -> None:
        self.write_record(
            "records/profile-updates/profile-update-beta.txt",
            f"""
            Record-ID: profile-update-beta
            Action: set_display_name
            Source-Identity-ID: {self.beta}
            Timestamp: 2026-03-18T00:00:00Z

            ClaimedBeta
            """,
        )
        self.write_record(
            "records/identity-links/link-alpha-beta.txt",
            f"""
            Record-ID: link-alpha-beta
            Action: merge_identity
            Source-Identity-ID: {self.alpha}
            Target-Identity-ID: {self.beta}
            Timestamp: 2026-03-18T01:00:00Z

            merge
            """,
        )
        self.write_record(
            "records/identity-links/link-beta-alpha.txt",
            f"""
            Record-ID: link-beta-alpha
            Action: merge_identity
            Source-Identity-ID: {self.beta}
            Target-Identity-ID: {self.alpha}
            Timestamp: 2026-03-18T01:01:00Z

            merge
            """,
        )

        status, _, body = self.get("/api/get_username_claim_cta", f"identity_id={self.alpha}")

        self.assertEqual(status, "200 OK")
        self.assertIn(f"Identity-ID: {self.alpha}", body)
        self.assertIn("Can-Claim-Username: yes", body)
        self.assertIn("Update-Href: /profiles/openpgp-alpha/update", body)

    def test_get_username_claim_cta_returns_not_found_for_unknown_identity(self) -> None:
        status, _, body = self.get("/api/get_username_claim_cta", "identity_id=openpgp:missing")

        self.assertEqual(status, "404 Not Found")
        self.assertIn("Resource: identity", body)
        self.assertIn("Identifier: openpgp:missing", body)


if __name__ == "__main__":
    unittest.main()
