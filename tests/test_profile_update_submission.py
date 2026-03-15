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

from forum_core.identity import build_bootstrap_payload, build_identity_id, fingerprint_from_public_key_text, identity_slug
from forum_read_only.web import application


class ProfileUpdateSubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tempdir.name)
        self.openpgp_module_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()

        self.run_command(
            [
                "git",
                "init",
            ],
            cwd=self.repo_root,
        )
        self.run_command(["git", "config", "user.name", "Codex Test"], cwd=self.repo_root)
        self.run_command(["git", "config", "user.email", "codex@example.com"], cwd=self.repo_root)

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

        with mock.patch.dict(os.environ, {"FORUM_REPO_ROOT": str(self.repo_root)}):
            body_text = b"".join(application(environ, start_response)).decode("utf-8")

        return (
            response["status"],
            dict(response["headers"]),
            body_text,
        )

    def test_api_update_profile_writes_record_and_profile_readback(self) -> None:
        payload_text = dedent(
            f"""
            Record-ID: profile-update-test-001
            Action: set_display_name
            Source-Identity-ID: {self.identity_id}
            Timestamp: 2026-03-14T12:00:00Z

            BrightName
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

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: profile-update-test-001", body)
        self.assertIn("Display-Name: BrightName", body)
        self.assertIn("Commit-ID:", body)
        self.assertTrue((self.repo_root / "records/profile-updates/profile-update-test-001.txt").exists())

        profile_status, _, profile_body = self.request(f"/profiles/{identity_slug(self.identity_id)}")

        self.assertEqual(profile_status, "200 OK")
        self.assertIn("BrightName", profile_body)

        log_result = self.run_command(["git", "log", "--oneline", "--max-count", "1"], cwd=self.repo_root)
        self.assertIn("update_profile: profile-update-test-001", log_result.stdout)


if __name__ == "__main__":
    unittest.main()
