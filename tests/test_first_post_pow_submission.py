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
from forum_web.web import application


class FirstPostPowSubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tempdir.name)
        (self.repo_root / "records" / "posts").mkdir(parents=True, exist_ok=True)
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
        return dedent(
            f"""
            Post-ID: {post_id}
            Board-Tags: general
            Subject: First post pow

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

    def create_request_body(self, payload_text: str, *, dry_run: bool, pow_stamp: str | None) -> bytes:
        request_payload: dict[str, object] = {
            "payload": payload_text,
            "signature": self.sign_payload(payload_text),
            "public_key": self.user_keys["publicKey"],
            "dry_run": dry_run,
        }
        if pow_stamp is not None:
            request_payload["pow_stamp"] = pow_stamp
        return json.dumps(request_payload).encode("utf-8")

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
            body=self.create_request_body(payload_text, dry_run=False, pow_stamp=None),
            extra_env={
                "FORUM_ENABLE_FIRST_POST_POW": "1",
                "FORUM_FIRST_POST_POW_DIFFICULTY": "8",
                "FORUM_ENABLE_THREAD_AUTO_REPLY": "0",
            },
        )

        self.assertEqual(status, "400 Bad Request")
        self.assertIn("Error-Code: bad_request", body)
        self.assertIn("Message: pow_stamp is required", body)

    def test_first_post_pow_accepts_valid_stamp(self) -> None:
        payload_text = self.build_thread_payload(post_id="thread-pow-valid-001")
        pow_stamp = self.solve_pow(post_id="thread-pow-valid-001", difficulty=8)

        status, _, body = self.request(
            "/api/create_thread",
            method="POST",
            body=self.create_request_body(payload_text, dry_run=False, pow_stamp=pow_stamp),
            extra_env={
                "FORUM_ENABLE_FIRST_POST_POW": "1",
                "FORUM_FIRST_POST_POW_DIFFICULTY": "8",
                "FORUM_ENABLE_THREAD_AUTO_REPLY": "0",
            },
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: thread-pow-valid-001", body)
        self.assertIn("Identity-Bootstrap-Created: yes", body)

    def test_first_post_pow_applies_to_dry_run_preview(self) -> None:
        payload_text = self.build_thread_payload(post_id="thread-pow-preview-001")

        status, _, body = self.request(
            "/api/create_thread",
            method="POST",
            body=self.create_request_body(payload_text, dry_run=True, pow_stamp=None),
            extra_env={
                "FORUM_ENABLE_FIRST_POST_POW": "1",
                "FORUM_FIRST_POST_POW_DIFFICULTY": "8",
                "FORUM_ENABLE_THREAD_AUTO_REPLY": "0",
            },
        )

        self.assertEqual(status, "400 Bad Request")
        self.assertIn("Message: pow_stamp is required", body)

    def test_existing_identity_bypasses_pow_requirement(self) -> None:
        self.write_identity_bootstrap()
        payload_text = self.build_thread_payload(post_id="thread-pow-established-001")

        status, _, body = self.request(
            "/api/create_thread",
            method="POST",
            body=self.create_request_body(payload_text, dry_run=False, pow_stamp=None),
            extra_env={
                "FORUM_ENABLE_FIRST_POST_POW": "1",
                "FORUM_FIRST_POST_POW_DIFFICULTY": "8",
                "FORUM_ENABLE_THREAD_AUTO_REPLY": "0",
            },
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: thread-pow-established-001", body)
        self.assertIn("Identity-Bootstrap-Created: no", body)


if __name__ == "__main__":
    unittest.main()
