from __future__ import annotations

import hashlib
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
from forum_core.proof_of_work import build_pow_message, count_leading_zero_bits
from forum_core.public_keys import resolve_canonical_public_key_path
from forum_web.web import application


class FirstPostPowSubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tempdir.name)
        (self.repo_root / "records" / "posts").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "records" / "posts" / "root-001.txt").write_text(
            dedent(
                """
                Post-ID: root-001
                Board-Tags: general
                Subject: Existing root

                Existing root body.
                """
            ).lstrip(),
            encoding="ascii",
        )
        self.openpgp_module_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()

        self.run_command(["git", "init"], cwd=self.repo_root)
        self.run_command(["git", "config", "user.name", "Codex Test"], cwd=self.repo_root)
        self.run_command(["git", "config", "user.email", "codex@example.com"], cwd=self.repo_root)

        self.user_keys = self.generate_signing_keypair("First Post Pow Test")
        self.fingerprint = fingerprint_from_public_key_text(self.user_keys["publicKey"])

    def tearDown(self) -> None:
        self.repo_tempdir.cleanup()

    def run_command(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

    def run_node_module(self, script: str) -> str:
        result = self.run_command(["node", "--input-type=module", "--eval", script])
        return result.stdout

    def generate_signing_keypair(self, name: str) -> dict[str, str]:
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

    def sign_payload(self, payload_text: str) -> str:
        script = f"""
import * as openpgp from {json.dumps(self.openpgp_module_url)};
const privateKey = await openpgp.readPrivateKey({{
  armoredKey: {json.dumps(self.user_keys["privateKey"])},
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

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        body: bytes = b"",
        extra_env: dict[str, str] | None = None,
    ) -> tuple[str, dict[str, str], str]:
        environ = {
            "PATH_INFO": path,
            "QUERY_STRING": "",
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

        with mock.patch.dict(os.environ, env, clear=False):
            body_text = b"".join(application(environ, start_response)).decode("utf-8")

        return response["status"], dict(response["headers"]), body_text

    def build_thread_payload(self, *, post_id: str) -> str:
        return self.build_thread_payload_with_pow(post_id=post_id, proof_of_work=None)

    def build_reply_payload(self, *, post_id: str) -> str:
        return dedent(
            f"""
            Post-ID: {post_id}
            Board-Tags: general
            Thread-ID: root-001
            Parent-ID: root-001

            Hello from the reply path.
            """
        ).lstrip()

    def build_thread_payload_with_pow(self, *, post_id: str, proof_of_work: str | None) -> str:
        proof_header = f"Proof-Of-Work: {proof_of_work}\n" if proof_of_work else ""
        return dedent(
            f"""
            Post-ID: {post_id}
            Board-Tags: general
            Subject: First post pow
            {proof_header}

            Hello from the first-post pow path.
            """
        ).lstrip()

    def solve_pow(self, *, post_id: str, difficulty: int) -> str:
        nonce = 0
        while True:
            candidate = f"{nonce:x}"
            digest = hashlib.sha256(
                build_pow_message(
                    signer_fingerprint=self.fingerprint,
                    post_id=post_id,
                    nonce=candidate,
                    difficulty=difficulty,
                )
            ).digest()
            if count_leading_zero_bits(digest) >= difficulty:
                return f"v1:{candidate}"
            nonce += 1

    def create_request_body(self, payload_text: str, *, dry_run: bool) -> bytes:
        request_payload: dict[str, object] = {
            "payload": payload_text,
            "signature": self.sign_payload(payload_text),
            "public_key": self.user_keys["publicKey"],
            "dry_run": dry_run,
        }
        return json.dumps(request_payload).encode("utf-8")

    def create_unsigned_request_body(self, payload_text: str, *, dry_run: bool) -> bytes:
        return json.dumps(
            {
                "payload": payload_text,
                "dry_run": dry_run,
            }
        ).encode("utf-8")

    def write_identity_bootstrap(self) -> None:
        identity_id = build_identity_id(self.fingerprint)
        record_id, payload = build_bootstrap_payload(
            identity_id=identity_id,
            signer_fingerprint=self.fingerprint,
            bootstrap_post_id="thread-existing-identity",
            bootstrap_thread_id="thread-existing-identity",
            public_key_text=self.user_keys["publicKey"],
        )
        path = self.repo_root / "records" / "identity" / f"{record_id}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="ascii")

    def test_first_post_pow_rejects_missing_stamp(self) -> None:
        payload_text = self.build_thread_payload(post_id="thread-pow-missing-001")

        status, _, body = self.request(
            "/api/create_thread",
            method="POST",
            body=self.create_request_body(payload_text, dry_run=False),
            extra_env={
                "FORUM_ENABLE_FIRST_POST_POW": "1",
                "FORUM_FIRST_POST_POW_DIFFICULTY": "8",
                "FORUM_ENABLE_THREAD_AUTO_REPLY": "0",
            },
        )

        self.assertEqual(status, "400 Bad Request")
        self.assertIn("Error-Code: bad_request", body)
        self.assertIn("Message: payload is missing Proof-Of-Work", body)

    def test_repeated_signed_threads_reuse_one_canonical_public_key_file(self) -> None:
        first_payload = self.build_thread_payload(post_id="thread-key-reuse-001")
        second_payload = self.build_thread_payload(post_id="thread-key-reuse-002")

        first_status, _, first_body = self.request(
            "/api/create_thread",
            method="POST",
            body=self.create_request_body(first_payload, dry_run=False),
            extra_env={"FORUM_ENABLE_FIRST_POST_POW": "0", "FORUM_ENABLE_THREAD_AUTO_REPLY": "0"},
        )
        second_status, _, second_body = self.request(
            "/api/create_thread",
            method="POST",
            body=self.create_request_body(second_payload, dry_run=False),
            extra_env={"FORUM_ENABLE_FIRST_POST_POW": "0", "FORUM_ENABLE_THREAD_AUTO_REPLY": "0"},
        )

        canonical_path = resolve_canonical_public_key_path(self.repo_root, self.fingerprint)
        relative_canonical_path = canonical_path.relative_to(self.repo_root)

        self.assertEqual(first_status, "200 OK")
        self.assertEqual(second_status, "200 OK")
        self.assertIn(f"Public-Key-Path: {relative_canonical_path}", first_body)
        self.assertIn(f"Public-Key-Path: {relative_canonical_path}", second_body)
        self.assertTrue(canonical_path.exists())
        self.assertFalse((self.repo_root / "records" / "posts" / "thread-key-reuse-001.txt.pub.asc").exists())
        self.assertFalse((self.repo_root / "records" / "posts" / "thread-key-reuse-002.txt.pub.asc").exists())

    def test_unsigned_post_rejected_when_fallback_flag_is_off(self) -> None:
        payload_text = self.build_thread_payload(post_id="thread-unsigned-disabled-001")

        status, _, body = self.request(
            "/api/create_thread",
            method="POST",
            body=self.create_unsigned_request_body(payload_text, dry_run=False),
            extra_env={"FORUM_ENABLE_THREAD_AUTO_REPLY": "0"},
        )

        self.assertEqual(status, "400 Bad Request")
        self.assertIn("Error-Code: bad_request", body)
        self.assertIn("Message: signature and public_key are required", body)

    def test_unsigned_post_accepted_when_fallback_flag_is_on(self) -> None:
        payload_text = self.build_thread_payload(post_id="thread-unsigned-enabled-001")

        status, _, body = self.request(
            "/api/create_thread",
            method="POST",
            body=self.create_unsigned_request_body(payload_text, dry_run=False),
            extra_env={
                "FORUM_ENABLE_THREAD_AUTO_REPLY": "0",
                "FORUM_ENABLE_UNSIGNED_POST_FALLBACK": "1",
            },
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: thread-unsigned-enabled-001", body)

    def test_unsigned_reply_rejected_when_fallback_flag_is_off(self) -> None:
        payload_text = self.build_reply_payload(post_id="reply-unsigned-disabled-001")

        status, _, body = self.request(
            "/api/create_reply",
            method="POST",
            body=self.create_unsigned_request_body(payload_text, dry_run=False),
        )

        self.assertEqual(status, "400 Bad Request")
        self.assertIn("Error-Code: bad_request", body)
        self.assertIn("Message: signature and public_key are required", body)

    def test_unsigned_reply_accepted_when_fallback_flag_is_on(self) -> None:
        payload_text = self.build_reply_payload(post_id="reply-unsigned-enabled-001")

        status, _, body = self.request(
            "/api/create_reply",
            method="POST",
            body=self.create_unsigned_request_body(payload_text, dry_run=False),
            extra_env={"FORUM_ENABLE_UNSIGNED_POST_FALLBACK": "1"},
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: reply-unsigned-enabled-001", body)

    def test_first_post_pow_accepts_valid_stamp(self) -> None:
        pow_stamp = self.solve_pow(post_id="thread-pow-valid-001", difficulty=8)
        payload_text = self.build_thread_payload_with_pow(
            post_id="thread-pow-valid-001",
            proof_of_work=pow_stamp,
        )

        status, _, body = self.request(
            "/api/create_thread",
            method="POST",
            body=self.create_request_body(payload_text, dry_run=False),
            extra_env={
                "FORUM_ENABLE_FIRST_POST_POW": "1",
                "FORUM_FIRST_POST_POW_DIFFICULTY": "8",
                "FORUM_ENABLE_THREAD_AUTO_REPLY": "0",
            },
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: thread-pow-valid-001", body)
        self.assertIn("Identity-Bootstrap-Created: yes", body)
        stored_post = (self.repo_root / "records" / "posts" / "thread-pow-valid-001.txt").read_text(encoding="ascii")
        self.assertIn(f"Proof-Of-Work: {pow_stamp}", stored_post)

    def test_first_post_pow_applies_to_dry_run_preview(self) -> None:
        payload_text = self.build_thread_payload(post_id="thread-pow-preview-001")

        status, _, body = self.request(
            "/api/create_thread",
            method="POST",
            body=self.create_request_body(payload_text, dry_run=True),
            extra_env={
                "FORUM_ENABLE_FIRST_POST_POW": "1",
                "FORUM_FIRST_POST_POW_DIFFICULTY": "8",
                "FORUM_ENABLE_THREAD_AUTO_REPLY": "0",
            },
        )

        self.assertEqual(status, "400 Bad Request")
        self.assertIn("Message: payload is missing Proof-Of-Work", body)

    def test_existing_identity_bypasses_pow_requirement(self) -> None:
        self.write_identity_bootstrap()
        payload_text = self.build_thread_payload(post_id="thread-pow-established-001")

        status, _, body = self.request(
            "/api/create_thread",
            method="POST",
            body=self.create_request_body(payload_text, dry_run=False),
            extra_env={
                "FORUM_ENABLE_FIRST_POST_POW": "1",
                "FORUM_FIRST_POST_POW_DIFFICULTY": "8",
                "FORUM_ENABLE_THREAD_AUTO_REPLY": "0",
            },
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: thread-pow-established-001", body)
        self.assertIn("Identity-Bootstrap-Created: no", body)

    def test_pow_requirement_endpoint_reports_first_post_state(self) -> None:
        request_body = json.dumps({"public_key": self.user_keys["publicKey"]}).encode("utf-8")

        status, headers, body = self.request(
            "/api/pow_requirement",
            method="POST",
            body=request_body,
            extra_env={
                "FORUM_ENABLE_FIRST_POST_POW": "1",
                "FORUM_FIRST_POST_POW_DIFFICULTY": "8",
            },
        )

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        payload = json.loads(body)
        self.assertTrue(payload["required"])
        self.assertEqual(payload["difficulty"], 8)
        self.assertEqual(payload["signer_fingerprint"], self.fingerprint)

        self.write_identity_bootstrap()

        status, _, body = self.request(
            "/api/pow_requirement",
            method="POST",
            body=request_body,
            extra_env={
                "FORUM_ENABLE_FIRST_POST_POW": "1",
                "FORUM_FIRST_POST_POW_DIFFICULTY": "8",
            },
        )

        self.assertEqual(status, "200 OK")
        payload = json.loads(body)
        self.assertFalse(payload["required"])


if __name__ == "__main__":
    unittest.main()
