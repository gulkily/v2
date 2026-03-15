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

from forum_cgi.auto_reply import AutoReplyError, AutoReplySigningError, thread_auto_reply_enabled
from forum_web.web import application


class ThreadAutoReplyTests(unittest.TestCase):
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

        self.user_keys = self.generate_signing_keypair("Thread Author Test")
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
        result = self.run_command(
            [
                "node",
                "--input-type=module",
                "--eval",
                script,
            ]
        )
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

    def build_thread_payload(self, *, post_id: str, subject: str, body_text: str) -> str:
        return dedent(
            f"""
            Post-ID: {post_id}
            Board-Tags: general
            Subject: {subject}

            {body_text}
            """
        ).lstrip()

    def create_thread_request_body(self, payload_text: str) -> bytes:
        signature_text = self.sign_payload(payload_text, self.user_keys["privateKey"])
        return json.dumps(
            {
                "payload": payload_text,
                "signature": signature_text,
                "public_key": self.user_keys["publicKey"],
                "dry_run": False,
            }
        ).encode("utf-8")

    def test_thread_auto_reply_enabled_parses_common_truthy_values(self) -> None:
        with mock.patch.dict(os.environ, {"FORUM_ENABLE_THREAD_AUTO_REPLY": "yes"}, clear=False):
            self.assertTrue(thread_auto_reply_enabled())
        with mock.patch.dict(os.environ, {"FORUM_ENABLE_THREAD_AUTO_REPLY": "0"}, clear=False):
            self.assertFalse(thread_auto_reply_enabled())

    def test_api_create_thread_reports_disabled_when_feature_flag_is_off(self) -> None:
        payload_text = self.build_thread_payload(
            post_id="thread-disabled-001",
            subject="Disabled auto reply",
            body_text="Hello from the disabled path.",
        )

        status, _, body = self.request(
            "/api/create_thread",
            method="POST",
            body=self.create_thread_request_body(payload_text),
            extra_env={"FORUM_ENABLE_THREAD_AUTO_REPLY": "0"},
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: thread-disabled-001", body)
        self.assertIn("Auto-Reply-Status: disabled", body)
        self.assertNotIn("Auto-Reply-Record-ID:", body)
        self.assertTrue((self.repo_root / "records" / "posts" / "thread-disabled-001.txt").exists())

    def test_api_create_thread_creates_auto_reply_when_feature_flag_is_on(self) -> None:
        payload_text = self.build_thread_payload(
            post_id="thread-enabled-001",
            subject="Enabled auto reply",
            body_text="Hello from the enabled path.",
        )

        with mock.patch("forum_cgi.auto_reply.run_llm", return_value="Helpful assistant reply.\n"):
            status, _, body = self.request(
                "/api/create_thread",
                method="POST",
                body=self.create_thread_request_body(payload_text),
                extra_env={
                    "FORUM_ENABLE_THREAD_AUTO_REPLY": "1",
                    "FORUM_THREAD_AUTO_REPLY_PRIVATE_KEY_PATH": "",
                    "FORUM_THREAD_AUTO_REPLY_PUBLIC_KEY_PATH": "",
                },
            )

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: thread-enabled-001", body)
        self.assertIn("Auto-Reply-Status: created", body)
        self.assertIn("Auto-Reply-Model: openai/gpt-4o-mini", body)
        auto_reply_record_id = body.split("Auto-Reply-Record-ID: ", 1)[1].splitlines()[0].strip()
        self.assertTrue((self.repo_root / "records" / "posts" / f"{auto_reply_record_id}.txt").exists())
        self.assertTrue((self.repo_root / "records" / "system" / "thread-auto-reply-private.asc").exists())
        self.assertTrue((self.repo_root / "records" / "system" / "thread-auto-reply-public.asc").exists())

        thread_status, _, thread_body = self.request("/threads/thread-enabled-001")
        self.assertEqual(thread_status, "200 OK")
        self.assertIn("Helpful assistant reply.", thread_body)
        self.assertIn("model-generated reply (openai/gpt-4o-mini)", thread_body)
        self.assertIn("[Model-generated reply via openai/gpt-4o-mini]", thread_body)

    def test_api_create_thread_keeps_root_thread_when_auto_reply_generation_fails(self) -> None:
        payload_text = self.build_thread_payload(
            post_id="thread-failed-001",
            subject="Failed auto reply",
            body_text="Hello from the failed path.",
        )

        with mock.patch(
            "forum_cgi.service.generate_thread_auto_reply",
            side_effect=AutoReplyError("assistant reply unavailable"),
        ):
            status, _, body = self.request(
                "/api/create_thread",
                method="POST",
                body=self.create_thread_request_body(payload_text),
                extra_env={
                    "FORUM_ENABLE_THREAD_AUTO_REPLY": "1",
                    "FORUM_THREAD_AUTO_REPLY_PRIVATE_KEY_PATH": "",
                    "FORUM_THREAD_AUTO_REPLY_PUBLIC_KEY_PATH": "",
                },
            )

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: thread-failed-001", body)
        self.assertIn("Auto-Reply-Status: failed", body)
        self.assertIn("Auto-Reply-Message: assistant reply unavailable", body)
        self.assertTrue((self.repo_root / "records" / "posts" / "thread-failed-001.txt").exists())
        post_files = sorted(path.name for path in (self.repo_root / "records" / "posts").glob("*.txt"))
        self.assertEqual(post_files, ["thread-failed-001.txt"])

    def test_api_create_thread_falls_back_to_unsigned_reply_when_signing_setup_fails(self) -> None:
        payload_text = self.build_thread_payload(
            post_id="thread-unsigned-001",
            subject="Unsigned fallback",
            body_text="Hello from the unsigned fallback path.",
        )

        with mock.patch("forum_cgi.auto_reply.run_llm", return_value="Unsigned assistant reply.\n"), mock.patch(
            "forum_cgi.auto_reply.generate_signing_keypair",
            side_effect=AutoReplySigningError("simulated key generation failure"),
        ):
            status, _, body = self.request(
                "/api/create_thread",
                method="POST",
                body=self.create_thread_request_body(payload_text),
                extra_env={"FORUM_ENABLE_THREAD_AUTO_REPLY": "1"},
            )

        self.assertEqual(status, "200 OK")
        self.assertIn("Record-ID: thread-unsigned-001", body)
        self.assertIn("Auto-Reply-Status: created_unsigned", body)
        self.assertIn("Auto-Reply-Message: assistant signing keys could not be prepared:", body)
        self.assertIn("Auto-Reply-Model: openai/gpt-4o-mini", body)
        auto_reply_record_id = body.split("Auto-Reply-Record-ID: ", 1)[1].splitlines()[0].strip()
        self.assertTrue((self.repo_root / "records" / "posts" / f"{auto_reply_record_id}.txt").exists())
        self.assertFalse((self.repo_root / "records" / "posts" / f"{auto_reply_record_id}.txt.asc").exists())
        self.assertFalse((self.repo_root / "records" / "posts" / f"{auto_reply_record_id}.txt.pub.asc").exists())

        thread_status, _, thread_body = self.request("/threads/thread-unsigned-001")
        self.assertEqual(thread_status, "200 OK")
        self.assertIn("Unsigned assistant reply.", thread_body)
        self.assertIn("model-generated reply (openai/gpt-4o-mini)", thread_body)


if __name__ == "__main__":
    unittest.main()
