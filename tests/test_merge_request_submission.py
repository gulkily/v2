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
from forum_core.merge_requests import derive_merge_request_states, load_merge_request_records, merge_request_records_dir
from forum_web.web import application


class MergeRequestSubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tempdir.name)
        self.openpgp_module_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()

        self.run_command(["git", "init"], cwd=self.repo_root)
        self.run_command(["git", "config", "user.name", "Codex Test"], cwd=self.repo_root)
        self.run_command(["git", "config", "user.email", "codex@example.com"], cwd=self.repo_root)

        self.alpha = self.generate_signing_keypair("Alpha")
        self.beta = self.generate_signing_keypair("Beta")
        self.gamma = self.generate_signing_keypair("Gamma")
        self.moderator = self.generate_signing_keypair("Moderator")
        for entry in (self.alpha, self.beta, self.gamma):
            record_id, payload = build_bootstrap_payload(
                identity_id=entry["identity_id"],
                signer_fingerprint=entry["fingerprint"],
                bootstrap_post_id=f"bootstrap-{entry['label'].lower()}",
                bootstrap_thread_id=f"bootstrap-{entry['label'].lower()}",
                public_key_text=entry["public_key"],
            )
            self.write_record(f"records/identity/{record_id}.txt", payload)

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

    def generate_signing_keypair(self, label: str) -> dict[str, str]:
        script = f"""
import * as openpgp from {json.dumps(self.openpgp_module_url)};
const generated = await openpgp.generateKey({{
  type: "ecc",
  curve: "ed25519",
  userIDs: [{{ name: {json.dumps(label)} }}],
  format: "armored",
}});
process.stdout.write(JSON.stringify({{
  privateKey: generated.privateKey,
  publicKey: generated.publicKey,
}}));
"""
        generated = json.loads(self.run_node_module(script))
        fingerprint = fingerprint_from_public_key_text(generated["publicKey"])
        identity_id = build_identity_id(fingerprint)
        return {
            "label": label,
            "private_key": generated["privateKey"],
            "public_key": generated["publicKey"],
            "fingerprint": fingerprint,
            "identity_id": identity_id,
        }

    def sign_payload(self, payload_text: str, private_key_text: str) -> str:
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

    def test_api_merge_request_request_then_target_approve(self) -> None:
        request_payload = dedent(
            f"""
            Record-ID: merge-request-001
            Action: request_merge
            Requester-Identity-ID: {self.alpha['identity_id']}
            Target-Identity-ID: {self.beta['identity_id']}
            Actor-Identity-ID: {self.alpha['identity_id']}
            Timestamp: 2026-03-17T23:00:00Z

            please merge
            """
        ).lstrip()
        request_signature = self.sign_payload(request_payload, self.alpha["private_key"])
        request_body = json.dumps(
            {
                "payload": request_payload,
                "signature": request_signature,
                "public_key": self.alpha["public_key"],
                "dry_run": False,
            }
        ).encode("utf-8")

        status, _, body = self.request("/api/merge_request", method="POST", body=request_body)

        self.assertEqual(status, "200 OK")
        self.assertIn("Action: request_merge", body)

        approve_payload = dedent(
            f"""
            Record-ID: merge-request-002
            Action: approve_merge
            Requester-Identity-ID: {self.alpha['identity_id']}
            Target-Identity-ID: {self.beta['identity_id']}
            Actor-Identity-ID: {self.beta['identity_id']}
            Timestamp: 2026-03-17T23:05:00Z

            """
        ).lstrip()
        approve_signature = self.sign_payload(approve_payload, self.beta["private_key"])
        approve_body = json.dumps(
            {
                "payload": approve_payload,
                "signature": approve_signature,
                "public_key": self.beta["public_key"],
                "dry_run": False,
            }
        ).encode("utf-8")

        approve_status, _, approve_response = self.request("/api/merge_request", method="POST", body=approve_body)

        self.assertEqual(approve_status, "200 OK")
        self.assertIn("Action: approve_merge", approve_response)

        states = derive_merge_request_states(load_merge_request_records(merge_request_records_dir(self.repo_root)))
        self.assertEqual(len(states), 1)
        self.assertTrue(states[0].active_merge)
        self.assertTrue(states[0].approved_by_target)

    def test_api_merge_request_allows_moderator_approval(self) -> None:
        request_payload = dedent(
            f"""
            Record-ID: merge-request-010
            Action: request_merge
            Requester-Identity-ID: {self.alpha['identity_id']}
            Target-Identity-ID: {self.beta['identity_id']}
            Actor-Identity-ID: {self.alpha['identity_id']}
            Timestamp: 2026-03-17T23:00:00Z

            """
        ).lstrip()
        request_signature = self.sign_payload(request_payload, self.alpha["private_key"])
        request_body = json.dumps(
            {
                "payload": request_payload,
                "signature": request_signature,
                "public_key": self.alpha["public_key"],
                "dry_run": False,
            }
        ).encode("utf-8")
        request_status, _, _ = self.request("/api/merge_request", method="POST", body=request_body)
        self.assertEqual(request_status, "200 OK")

        moderator_payload = dedent(
            f"""
            Record-ID: merge-request-011
            Action: moderator_approve_merge
            Requester-Identity-ID: {self.alpha['identity_id']}
            Target-Identity-ID: {self.beta['identity_id']}
            Actor-Identity-ID: {self.moderator['identity_id']}
            Timestamp: 2026-03-17T23:04:00Z

            """
        ).lstrip()
        moderator_signature = self.sign_payload(moderator_payload, self.moderator["private_key"])
        moderator_body = json.dumps(
            {
                "payload": moderator_payload,
                "signature": moderator_signature,
                "public_key": self.moderator["public_key"],
                "dry_run": False,
            }
        ).encode("utf-8")
        moderator_status, _, moderator_response = self.request(
            "/api/merge_request",
            method="POST",
            body=moderator_body,
            extra_env={"FORUM_MODERATOR_FINGERPRINTS": self.moderator["fingerprint"]},
        )

        self.assertEqual(moderator_status, "200 OK")
        self.assertIn("Action: moderator_approve_merge", moderator_response)

        states = derive_merge_request_states(load_merge_request_records(merge_request_records_dir(self.repo_root)))
        self.assertTrue(states[0].approved_by_moderator)
        self.assertTrue(states[0].active_merge)

    def test_api_merge_request_allows_approval_by_member_of_target_resolved_set(self) -> None:
        self.write_record(
            "records/identity-links/link-beta-gamma.txt",
            dedent(
                f"""
                Record-ID: link-beta-gamma
                Action: merge_identity
                Source-Identity-ID: {self.beta['identity_id']}
                Target-Identity-ID: {self.gamma['identity_id']}
                Timestamp: 2026-03-17T22:00:00Z

                merge
                """
            ).lstrip(),
        )
        self.write_record(
            "records/identity-links/link-gamma-beta.txt",
            dedent(
                f"""
                Record-ID: link-gamma-beta
                Action: merge_identity
                Source-Identity-ID: {self.gamma['identity_id']}
                Target-Identity-ID: {self.beta['identity_id']}
                Timestamp: 2026-03-17T22:01:00Z

                merge
                """
            ).lstrip(),
        )

        request_payload = dedent(
            f"""
            Record-ID: merge-request-020
            Action: request_merge
            Requester-Identity-ID: {self.alpha['identity_id']}
            Target-Identity-ID: {self.beta['identity_id']}
            Actor-Identity-ID: {self.alpha['identity_id']}
            Timestamp: 2026-03-17T23:00:00Z

            please merge
            """
        ).lstrip()
        request_signature = self.sign_payload(request_payload, self.alpha["private_key"])
        request_body = json.dumps(
            {
                "payload": request_payload,
                "signature": request_signature,
                "public_key": self.alpha["public_key"],
                "dry_run": False,
            }
        ).encode("utf-8")
        request_status, _, _ = self.request("/api/merge_request", method="POST", body=request_body)
        self.assertEqual(request_status, "200 OK")

        approve_payload = dedent(
            f"""
            Record-ID: merge-request-021
            Action: approve_merge
            Requester-Identity-ID: {self.alpha['identity_id']}
            Target-Identity-ID: {self.beta['identity_id']}
            Actor-Identity-ID: {self.gamma['identity_id']}
            Timestamp: 2026-03-17T23:05:00Z

            """
        ).lstrip()
        approve_signature = self.sign_payload(approve_payload, self.gamma["private_key"])
        approve_body = json.dumps(
            {
                "payload": approve_payload,
                "signature": approve_signature,
                "public_key": self.gamma["public_key"],
                "dry_run": False,
            }
        ).encode("utf-8")

        approve_status, _, approve_response = self.request("/api/merge_request", method="POST", body=approve_body)

        self.assertEqual(approve_status, "200 OK")
        self.assertIn("Action: approve_merge", approve_response)

        states = derive_merge_request_states(load_merge_request_records(merge_request_records_dir(self.repo_root)))
        self.assertEqual(len(states), 1)
        self.assertTrue(states[0].active_merge)
        self.assertTrue(states[0].approved_by_target)


if __name__ == "__main__":
    unittest.main()
