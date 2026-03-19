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
from forum_core.operation_events import load_recent_operations
from forum_web.web import application


class RequestOperationEventsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tempdir.name)
        self.openpgp_module_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        self.run_command(["git", "init"], cwd=self.repo_root)
        self.run_command(["git", "config", "user.name", "Codex Test"], cwd=self.repo_root)
        self.run_command(["git", "config", "user.email", "codex@example.com"], cwd=self.repo_root)
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: Hello

            Body.
            """,
        )
        self.write_record(
            "records/instance/public.txt",
            """
            Instance-Name: Demo instance
            Admin-Name: Demo operator
            Admin-Contact: operator@example.invalid
            Retention-Policy: Keep canonical records in git.
            Install-Date: 2026-03-15

            Demo instance summary.
            """,
        )
        self.run_command(["git", "add", "."], cwd=self.repo_root)
        self.run_command(["git", "commit", "-m", "initial"], cwd=self.repo_root)
        generated = self.generate_signing_keypair()
        self.private_key_text = generated["privateKey"]
        self.public_key_text = generated["publicKey"]
        fingerprint = fingerprint_from_public_key_text(self.public_key_text)
        self.identity_id = build_identity_id(fingerprint)
        bootstrap_record_id, bootstrap_payload = build_bootstrap_payload(
            identity_id=self.identity_id,
            signer_fingerprint=fingerprint,
            bootstrap_post_id="root-001",
            bootstrap_thread_id="root-001",
            public_key_text=self.public_key_text,
        )
        self.write_record(f"records/identity/{bootstrap_record_id}.txt", bootstrap_payload)
        self.run_command(["git", "add", "."], cwd=self.repo_root)
        self.run_command(["git", "commit", "-m", "add identity bootstrap"], cwd=self.repo_root)

    def tearDown(self) -> None:
        self.repo_tempdir.cleanup()

    def run_command(self, command: list[str], *, cwd: Path | None = None, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
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
        return self.run_command(["node", "--input-type=module", "--eval", script]).stdout

    def generate_signing_keypair(self) -> dict[str, str]:
        script = f"""
import * as openpgp from {json.dumps(self.openpgp_module_url)};
const generated = await openpgp.generateKey({{
  type: "ecc",
  curve: "ed25519",
  userIDs: [{{ name: "Request Operation Test" }}],
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
  armoredKey: {json.dumps(self.private_key_text)},
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

    def request(self, path: str, *, method: str = "GET", body: bytes = b"") -> tuple[str, dict[str, str], str]:
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

        env = {
            "FORUM_REPO_ROOT": str(self.repo_root),
            "FORUM_ENABLE_FIRST_POST_POW": "0",
            "FORUM_ENABLE_THREAD_AUTO_REPLY": "0",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            body_text = b"".join(application(environ, start_response)).decode("utf-8")

        return response["status"], dict(response["headers"]), body_text

    def test_get_request_creates_completed_operation_record(self) -> None:
        status, _, _ = self.request("/instance/")

        self.assertEqual(status, "200 OK")
        operations = load_recent_operations(self.repo_root)
        instance_operation = next(event for event in operations if event.operation_name == "GET /instance/")
        self.assertEqual(instance_operation.state, "completed")
        self.assertEqual(instance_operation.metadata["path"], "/instance/")

    def test_create_thread_request_persists_phase_timings_in_request_record(self) -> None:
        payload_text = dedent(
            """
            Post-ID: thread-request-001
            Board-Tags: general
            Subject: Request timing

            Body.
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

        status, _, _ = self.request("/api/create_thread", method="POST", body=request_body)

        self.assertEqual(status, "200 OK")
        operations = load_recent_operations(self.repo_root)
        create_thread_operation = next(event for event in operations if event.operation_name == "POST /api/create_thread")
        self.assertEqual(create_thread_operation.state, "completed")
        step_names = tuple(step.name for step in create_thread_operation.steps)
        self.assertIn("parse_and_validate_thread", step_names)
        self.assertIn("git_commit", step_names)
        self.assertIn("post_index_refresh", step_names)


if __name__ == "__main__":
    unittest.main()
