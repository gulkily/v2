from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_core.identity import build_bootstrap_payload, build_identity_id, fingerprint_from_public_key_text, identity_slug
from forum_core.post_index import ensure_post_index_current, load_indexed_username_roots
from forum_core.public_keys import resolve_canonical_public_key_path
from tests.helpers import ForumRepoTestCase


class ProfileUpdateSubmissionTests(ForumRepoTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.openpgp_module_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()

        self.init_git_repo(user_name="Codex Test", user_email="codex@example.com")

        generated = self.generate_signing_keypair()
        self.private_key_text = generated["privateKey"]
        self.public_key_text = generated["publicKey"]
        self.fingerprint = fingerprint_from_public_key_text(self.public_key_text)
        self.identity_id = build_identity_id(self.fingerprint)
        bootstrap_record_id, bootstrap_payload = build_bootstrap_payload(
            identity_id=self.identity_id,
            signer_fingerprint=self.fingerprint,
            bootstrap_post_id="root-identity",
            bootstrap_thread_id="root-identity",
            public_key_text=self.public_key_text,
        )
        self.write_record(
            f"records/identity/{bootstrap_record_id}.txt",
            bootstrap_payload,
        )

    def run_node_module(self, script: str) -> str:
        result = self.run_command(
            [
                "node",
                "--input-type=module",
                "--eval",
                script,
            ]
        )
        return result.stdout

    def generate_signing_keypair(self) -> dict[str, str]:
        script = f"""
import * as openpgp from {json.dumps(self.openpgp_module_url)};
const generated = await openpgp.generateKey({{
  type: "ecc",
  curve: "ed25519",
  userIDs: [{{ name: "Profile Update Test" }}],
  format: "armored",
}});
process.stdout.write(JSON.stringify({{
  privateKey: generated.privateKey,
  publicKey: generated.publicKey,
}}));
"""
        return json.loads(self.run_node_module(script))

    def sign_payload(self, payload_text: str) -> str:
        return self.sign_payload_with_private_key(payload_text, self.private_key_text)

    def sign_payload_with_private_key(self, payload_text: str, private_key_text: str) -> str:
        script = f"""
import * as openpgp from {json.dumps(self.openpgp_module_url)};
const privateKey = await openpgp.readPrivateKey({{
  armoredKey: {json.dumps(private_key_text)},
}});
const message = await openpgp.createMessage({{
  text: {json.dumps(payload_text)},
}});
const signature = await openpgp.sign({{
  message,
  signingKeys: privateKey,
  detached: true,
  format: "armored",
}});
process.stdout.write(signature);
"""
        return self.run_node_module(script)

    def request(self, path: str, *, method: str = "GET", body: bytes = b"") -> tuple[str, dict[str, str], str]:
        status, headers, response_body = super().request(path, method=method, body=body)
        return status, headers, str(response_body)

    def test_api_update_profile_writes_record_and_profile_readback(self) -> None:
        payload_text = dedent(
            f"""
            Record-ID: profile-update-test-001
            Action: set_display_name
            Source-Identity-ID: {self.identity_id}
            Timestamp: 2026-03-14T12:00:00Z

            bright-name
            """
        ).lstrip()
        signature_text = self.sign_payload(payload_text)
        request_body = json.dumps(
            {
                "payload": payload_text,
                "signature": signature_text,
                "public_key": self.public_key_text,
                "dry_run": False,
            }
        ).encode("utf-8")

        with self.assertLogs("forum_cgi.profile_updates", level="INFO") as captured_logs:
            status, _, body = self.request("/api/update_profile", method="POST", body=request_body)

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: profile-update-test-001", body)
        self.assertIn("Display-Name: bright-name", body)
        self.assertIn("Commit-ID:", body)
        self.assertTrue((self.repo_root / "records/profile-updates/profile-update-test-001.txt").exists())
        self.assertEqual(len(captured_logs.output), 1)
        timing_message = captured_logs.output[0]
        self.assertIn("update_profile timings for profile-update-test-001:", timing_message)
        self.assertIn("parse_profile_update=", timing_message)
        self.assertIn("verify_detached_signature=", timing_message)
        self.assertIn("validate_profile_update=", timing_message)
        self.assertIn("git_add=", timing_message)
        self.assertIn("git_commit=", timing_message)
        self.assertIn("git_rev_parse=", timing_message)
        self.assertIn("post_index_refresh=", timing_message)

        profile_status, _, profile_body = self.request(f"/profiles/{identity_slug(self.identity_id)}")

        self.assertEqual(profile_status, "200 OK")
        self.assertIn("bright-name", profile_body)

        log_result = self.run_command(["git", "log", "--oneline", "--max-count", "1"], cwd=self.repo_root)
        self.assertIn("update_profile: profile-update-test-001", log_result.stdout)

    def test_api_update_profile_reuses_canonical_public_key_storage(self) -> None:
        payload_text = dedent(
            f"""
            Record-ID: profile-update-test-003
            Action: set_display_name
            Source-Identity-ID: {self.identity_id}
            Timestamp: 2026-03-14T12:02:00Z

            reused-name
            """
        ).lstrip()
        signature_text = self.sign_payload(payload_text)
        request_body = json.dumps(
            {
                "payload": payload_text,
                "signature": signature_text,
                "public_key": self.public_key_text,
                "dry_run": False,
            }
        ).encode("utf-8")

        status, _, body = self.request("/api/update_profile", method="POST", body=request_body)

        canonical_path = resolve_canonical_public_key_path(self.repo_root, self.fingerprint)
        relative_canonical_path = canonical_path.relative_to(self.repo_root)

        self.assertEqual(status, "200 OK")
        self.assertIn(f"Public-Key-Path: {relative_canonical_path}", body)
        self.assertTrue(canonical_path.exists())
        self.assertFalse((self.repo_root / "records" / "profile-updates" / "profile-update-test-003.txt.pub.asc").exists())

    def test_api_update_profile_rejects_invalid_username_shape(self) -> None:
        payload_text = dedent(
            f"""
            Record-ID: profile-update-test-002
            Action: set_display_name
            Source-Identity-ID: {self.identity_id}
            Timestamp: 2026-03-14T12:01:00Z

            <script>alert()</script>
            """
        ).lstrip()
        signature_text = self.sign_payload(payload_text)
        request_body = json.dumps(
            {
                "payload": payload_text,
                "signature": signature_text,
                "public_key": self.public_key_text,
                "dry_run": False,
            }
        ).encode("utf-8")

        status, _, body = self.request("/api/update_profile", method="POST", body=request_body)

        self.assertEqual(status, "400 Bad Request")
        self.assertIn("display name must use lowercase ASCII letters, digits, and single hyphens only", body)

    def test_api_update_profile_refreshes_username_index_without_full_rebuild(self) -> None:
        ensure_post_index_current(self.repo_root).connection.close()
        payload_text = dedent(
            f"""
            Record-ID: profile-update-test-004
            Action: set_display_name
            Source-Identity-ID: {self.identity_id}
            Timestamp: 2026-03-14T12:03:00Z

            bright-name
            """
        ).lstrip()
        signature_text = self.sign_payload(payload_text)
        request_body = json.dumps(
            {
                "payload": payload_text,
                "signature": signature_text,
                "public_key": self.public_key_text,
                "dry_run": False,
            }
        ).encode("utf-8")

        with mock.patch(
            "forum_core.post_index.rebuild_post_index",
            side_effect=AssertionError("full rebuild should not run for profile update refresh when index exists"),
        ):
            status, _, body = self.request("/api/update_profile", method="POST", body=request_body)

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: profile-update-test-004", body)
        roots = load_indexed_username_roots(self.repo_root)
        self.assertEqual(roots["bright-name"].claim_record_id, "profile-update-test-004")

    def test_api_update_profile_rejects_second_claim_from_same_identity(self) -> None:
        first_payload_text = dedent(
            f"""
            Record-ID: profile-update-test-005
            Action: set_display_name
            Source-Identity-ID: {self.identity_id}
            Timestamp: 2026-03-14T12:04:00Z

            first-name
            """
        ).lstrip()
        first_request_body = json.dumps(
            {
                "payload": first_payload_text,
                "signature": self.sign_payload(first_payload_text),
                "public_key": self.public_key_text,
                "dry_run": False,
            }
        ).encode("utf-8")
        with mock.patch.dict(os.environ, {"FORUM_PREVENT_DUPLICATE_USERNAMES": "0"}, clear=False):
            first_status, _, _ = self.request("/api/update_profile", method="POST", body=first_request_body)

        second_payload_text = dedent(
            f"""
            Record-ID: profile-update-test-006
            Action: set_display_name
            Source-Identity-ID: {self.identity_id}
            Timestamp: 2026-03-14T12:05:00Z

            second-name
            """
        ).lstrip()
        second_request_body = json.dumps(
            {
                "payload": second_payload_text,
                "signature": self.sign_payload(second_payload_text),
                "public_key": self.public_key_text,
                "dry_run": False,
            }
        ).encode("utf-8")
        with mock.patch.dict(os.environ, {"FORUM_PREVENT_DUPLICATE_USERNAMES": "0"}, clear=False):
            second_status, _, second_body = self.request("/api/update_profile", method="POST", body=second_request_body)

        self.assertEqual(first_status, "200 OK")
        self.assertEqual(second_status, "403 Forbidden")
        self.assertIn("Error-Code: forbidden", second_body)
        self.assertIn("This account has already claimed a username.", second_body)

        profile_status, _, profile_body = self.request(f"/profiles/{identity_slug(self.identity_id)}")

        self.assertEqual(profile_status, "200 OK")
        self.assertIn("first-name", profile_body)
        self.assertNotIn("second-name", profile_body)

        self.assertFalse((self.repo_root / "records/profile-updates/profile-update-test-006.txt").exists())

    def test_api_update_profile_allows_duplicate_username_when_flag_is_off(self) -> None:
        shared_name = "shared-name"
        first_generated = self.generate_signing_keypair()
        first_identity_id = build_identity_id(fingerprint_from_public_key_text(first_generated["publicKey"]))
        second_generated = self.generate_signing_keypair()
        second_identity_id = build_identity_id(fingerprint_from_public_key_text(second_generated["publicKey"]))

        for index, (identity_id, public_key_text) in enumerate(
            (
                (first_identity_id, first_generated["publicKey"]),
                (second_identity_id, second_generated["publicKey"]),
            ),
            start=1,
        ):
            bootstrap_record_id, bootstrap_payload = build_bootstrap_payload(
                identity_id=identity_id,
                signer_fingerprint=fingerprint_from_public_key_text(public_key_text),
                bootstrap_post_id=f"root-identity-{index}",
                bootstrap_thread_id=f"root-identity-{index}",
                public_key_text=public_key_text,
            )
            self.write_record(f"records/identity/{bootstrap_record_id}.txt", bootstrap_payload)

        first_payload_text = dedent(
            f"""
            Record-ID: profile-update-test-007
            Action: set_display_name
            Source-Identity-ID: {first_identity_id}
            Timestamp: 2026-03-14T12:06:00Z

            {shared_name}
            """
        ).lstrip()
        first_request_body = json.dumps(
            {
                "payload": first_payload_text,
                "signature": self.sign_payload_with_private_key(first_payload_text, first_generated["privateKey"]),
                "public_key": first_generated["publicKey"],
                "dry_run": False,
            }
        ).encode("utf-8")
        with mock.patch.dict(os.environ, {"FORUM_PREVENT_DUPLICATE_USERNAMES": "0"}, clear=False):
            first_status, _, _ = self.request("/api/update_profile", method="POST", body=first_request_body)

        second_payload_text = dedent(
            f"""
            Record-ID: profile-update-test-008
            Action: set_display_name
            Source-Identity-ID: {second_identity_id}
            Timestamp: 2026-03-14T12:07:00Z

            {shared_name}
            """
        ).lstrip()
        second_request_body = json.dumps(
            {
                "payload": second_payload_text,
                "signature": self.sign_payload_with_private_key(second_payload_text, second_generated["privateKey"]),
                "public_key": second_generated["publicKey"],
                "dry_run": False,
            }
        ).encode("utf-8")
        with mock.patch.dict(os.environ, {"FORUM_PREVENT_DUPLICATE_USERNAMES": "0"}, clear=False):
            second_status, _, second_body = self.request("/api/update_profile", method="POST", body=second_request_body)

        self.assertEqual(first_status, "200 OK")
        self.assertEqual(second_status, "200 OK")
        self.assertIn("Record-ID: profile-update-test-008", second_body)

    def test_api_update_profile_rejects_duplicate_username_when_flag_is_on(self) -> None:
        shared_name = "shared-name"
        first_generated = self.generate_signing_keypair()
        first_identity_id = build_identity_id(fingerprint_from_public_key_text(first_generated["publicKey"]))
        second_generated = self.generate_signing_keypair()
        second_identity_id = build_identity_id(fingerprint_from_public_key_text(second_generated["publicKey"]))

        for index, (identity_id, public_key_text) in enumerate(
            (
                (first_identity_id, first_generated["publicKey"]),
                (second_identity_id, second_generated["publicKey"]),
            ),
            start=1,
        ):
            bootstrap_record_id, bootstrap_payload = build_bootstrap_payload(
                identity_id=identity_id,
                signer_fingerprint=fingerprint_from_public_key_text(public_key_text),
                bootstrap_post_id=f"root-identity-flag-{index}",
                bootstrap_thread_id=f"root-identity-flag-{index}",
                public_key_text=public_key_text,
            )
            self.write_record(f"records/identity/{bootstrap_record_id}.txt", bootstrap_payload)

        first_payload_text = dedent(
            f"""
            Record-ID: profile-update-test-009
            Action: set_display_name
            Source-Identity-ID: {first_identity_id}
            Timestamp: 2026-03-14T12:08:00Z

            {shared_name}
            """
        ).lstrip()
        first_request_body = json.dumps(
            {
                "payload": first_payload_text,
                "signature": self.sign_payload_with_private_key(first_payload_text, first_generated["privateKey"]),
                "public_key": first_generated["publicKey"],
                "dry_run": False,
            }
        ).encode("utf-8")

        second_payload_text = dedent(
            f"""
            Record-ID: profile-update-test-010
            Action: set_display_name
            Source-Identity-ID: {second_identity_id}
            Timestamp: 2026-03-14T12:09:00Z

            {shared_name}
            """
        ).lstrip()
        second_request_body = json.dumps(
            {
                "payload": second_payload_text,
                "signature": self.sign_payload_with_private_key(second_payload_text, second_generated["privateKey"]),
                "public_key": second_generated["publicKey"],
                "dry_run": False,
            }
        ).encode("utf-8")

        with mock.patch.dict(os.environ, {"FORUM_PREVENT_DUPLICATE_USERNAMES": "yes"}, clear=False):
            first_status, _, _ = self.request("/api/update_profile", method="POST", body=first_request_body)
            second_status, _, second_body = self.request("/api/update_profile", method="POST", body=second_request_body)

        self.assertEqual(first_status, "200 OK")
        self.assertEqual(second_status, "409 Conflict")
        self.assertIn("Error-Code: conflict", second_body)
        self.assertIn("That username is already taken. Choose a different username.", second_body)
        self.assertNotIn("FORUM_PREVENT_DUPLICATE_USERNAMES", second_body)
        self.assertFalse((self.repo_root / "records/profile-updates/profile-update-test-010.txt").exists())


if __name__ == "__main__":
    unittest.main()
