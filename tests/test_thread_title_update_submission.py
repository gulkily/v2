from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_core.identity import build_bootstrap_payload, build_identity_id, fingerprint_from_public_key_text
from forum_web.web import application


class ThreadTitleUpdateSubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tempdir.name)
        self.openpgp_module_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()

        self.run_command(["git", "init"], cwd=self.repo_root)
        self.run_command(["git", "config", "user.name", "Codex Test"], cwd=self.repo_root)
        self.run_command(["git", "config", "user.email", "codex@example.com"], cwd=self.repo_root)

        owner = self.generate_signing_keypair(name="Owner")
        self.owner_private_key_text = owner["privateKey"]
        self.owner_public_key_text = owner["publicKey"]
        self.owner_fingerprint = fingerprint_from_public_key_text(self.owner_public_key_text)
        self.owner_identity_id = build_identity_id(self.owner_fingerprint)
        bootstrap_record_id, bootstrap_payload = build_bootstrap_payload(
            identity_id=self.owner_identity_id,
            signer_fingerprint=self.owner_fingerprint,
            bootstrap_post_id="thread-001",
            bootstrap_thread_id="thread-001",
            public_key_text=self.owner_public_key_text,
        )
        self.write_record(f"records/identity/{bootstrap_record_id}.txt", bootstrap_payload)
        self.write_record(
            "records/posts/thread-001.txt",
            """
            Post-ID: thread-001
            Board-Tags: general
            Subject: Original title

            First post body
            """,
        )
        self.write_record("records/posts/thread-001.txt.pub.asc", self.owner_public_key_text)
        self.run_command(["git", "add", "."], cwd=self.repo_root)
        self.run_command(["git", "commit", "-m", "Seed thread"], cwd=self.repo_root)

        other = self.generate_signing_keypair(name="Other")
        self.other_private_key_text = other["privateKey"]
        self.other_public_key_text = other["PublicKey"] if "PublicKey" in other else other["publicKey"]
        self.other_fingerprint = fingerprint_from_public_key_text(self.other_public_key_text)

    def tearDown(self) -> None:
        self.repo_tempdir.cleanup()

    def run_command(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=cwd,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

    def run_node_module(self, script: str) -> str:
        result = self.run_command(["node", "--input-type=module", "--eval", script])
        return result.stdout

    def generate_signing_keypair(self, *, name: str) -> dict[str, str]:
        script = f"""
import * as openpgp from {json.dumps(self.openpgp_module_url)};
const generated = await openpgp.generateKey({{
  type: "ecc",
  curve: "ed25519",
  userIDs: [{{ name: {json.dumps(name)} }}],
  format: "armored",
}});
process.stdout.write(JSON.stringify({{
  privateKey: generated.privateKey,
  publicKey: generated.publicKey,
}}));
"""
        return json.loads(self.run_node_module(script))

    def sign_payload(self, payload_text: str, *, private_key_text: str) -> str:
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

    def write_record(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        body: bytes = b"",
        query_string: str = "",
        extra_env: dict[str, str] | None = None,
    ) -> tuple[str, dict[str, str], str]:
        environ = {
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
            "REQUEST_METHOD": method,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": BytesIO(body),
        }
        response: dict[str, object] = {}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = status
            response["headers"] = headers

        env = {"FORUM_REPO_ROOT": str(self.repo_root)}
        if extra_env:
            env.update(extra_env)
        with mock.patch.dict(os.environ, env):
            body_text = b"".join(application(environ, start_response)).decode("utf-8")

        return response["status"], dict(response["headers"]), body_text

    def test_api_update_thread_title_allows_owner(self) -> None:
        payload_text = dedent(
            """
            Record-ID: thread-title-update-001
            Thread-ID: thread-001
            Timestamp: 2026-03-28T12:00:00Z

            Better title
            """
        ).lstrip()
        signature_text = self.sign_payload(payload_text, private_key_text=self.owner_private_key_text)
        request_body = json.dumps(
            {
                "payload": payload_text,
                "signature": signature_text,
                "public_key": self.owner_public_key_text,
                "dry_run": False,
            }
        ).encode("utf-8")

        with self.assertLogs("forum_cgi.thread_title_updates", level="INFO") as captured_logs:
            status, _, body = self.request("/api/update_thread_title", method="POST", body=request_body)

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: thread-title-update-001", body)
        self.assertIn("Thread-ID: thread-001", body)
        self.assertIn("Title: Better title", body)
        self.assertTrue((self.repo_root / "records/thread-title-updates/thread-title-update-001.txt").exists())
        self.assertEqual(len(captured_logs.output), 1)
        self.assertIn("update_thread_title timings for thread-title-update-001:", captured_logs.output[0])
        root_text = (self.repo_root / "records/posts/thread-001.txt").read_text(encoding="ascii")
        self.assertIn("Subject: Original title", root_text)

    def test_api_update_thread_title_rejects_non_owner_when_flag_is_off(self) -> None:
        payload_text = dedent(
            """
            Record-ID: thread-title-update-002
            Thread-ID: thread-001
            Timestamp: 2026-03-28T12:01:00Z

            Not allowed
            """
        ).lstrip()
        signature_text = self.sign_payload(payload_text, private_key_text=self.other_private_key_text)
        request_body = json.dumps(
            {
                "payload": payload_text,
                "signature": signature_text,
                "public_key": self.other_public_key_text,
                "dry_run": False,
            }
        ).encode("utf-8")

        status, _, body = self.request("/api/update_thread_title", method="POST", body=request_body)

        self.assertEqual(status, "403 Forbidden")
        self.assertIn("signer is not allowed to update this thread title", body)

    def test_api_update_thread_title_allows_any_signed_user_when_flag_is_on(self) -> None:
        payload_text = dedent(
            """
            Record-ID: thread-title-update-003
            Thread-ID: thread-001
            Timestamp: 2026-03-28T12:02:00Z

            Community retitle
            """
        ).lstrip()
        signature_text = self.sign_payload(payload_text, private_key_text=self.other_private_key_text)
        request_body = json.dumps(
            {
                "payload": payload_text,
                "signature": signature_text,
                "public_key": self.other_public_key_text,
                "dry_run": False,
            }
        ).encode("utf-8")

        status, _, body = self.request(
            "/api/update_thread_title",
            method="POST",
            body=request_body,
            extra_env={"FORUM_ENABLE_THREAD_TITLE_ANY_USER_EDIT": "1"},
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: thread-title-update-003", body)
        self.assertIn("Title: Community retitle", body)

    def test_api_update_thread_title_allows_configured_moderator(self) -> None:
        payload_text = dedent(
            """
            Record-ID: thread-title-update-004
            Thread-ID: thread-001
            Timestamp: 2026-03-28T12:03:00Z

            Moderator retitle
            """
        ).lstrip()
        signature_text = self.sign_payload(payload_text, private_key_text=self.other_private_key_text)
        request_body = json.dumps(
            {
                "payload": payload_text,
                "signature": signature_text,
                "public_key": self.other_public_key_text,
                "dry_run": False,
            }
        ).encode("utf-8")

        status, _, body = self.request(
            "/api/update_thread_title",
            method="POST",
            body=request_body,
            extra_env={"FORUM_MODERATOR_FINGERPRINTS": self.other_fingerprint},
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Title: Moderator retitle", body)

    def test_owner_update_keeps_root_subject_unchanged_while_api_reports_current_title(self) -> None:
        payload_text = dedent(
            """
            Record-ID: thread-title-update-005
            Thread-ID: thread-001
            Timestamp: 2026-03-28T12:04:00Z

            API-visible rename
            """
        ).lstrip()
        signature_text = self.sign_payload(payload_text, private_key_text=self.owner_private_key_text)
        request_body = json.dumps(
            {
                "payload": payload_text,
                "signature": signature_text,
                "public_key": self.owner_public_key_text,
                "dry_run": False,
            }
        ).encode("utf-8")

        status, _, _ = self.request("/api/update_thread_title", method="POST", body=request_body)
        self.assertEqual(status, "200 OK")

        root_text = (self.repo_root / "records/posts/thread-001.txt").read_text(encoding="ascii")
        self.assertIn("Subject: Original title", root_text)

        thread_status, _, thread_body = self.request("/api/get_thread", query_string="thread_id=thread-001")
        self.assertEqual(thread_status, "200 OK")
        self.assertIn("Current-Title: API-visible rename", thread_body)
        self.assertIn("Subject: Original title", thread_body)


if __name__ == "__main__":
    unittest.main()
