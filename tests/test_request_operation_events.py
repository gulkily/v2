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
from forum_core.operation_events import load_recent_operations
from forum_core.post_index import PostIndexReadiness, ensure_post_index_current
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
        ensure_post_index_current(self.repo_root).connection.close()

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

    def request(self, path: str, *, method: str = "GET", body: bytes = b"", query_string: str = "") -> tuple[str, dict[str, str], str]:
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

    def test_activity_request_records_view_metadata_and_timing_steps(self) -> None:
        status, _, _ = self.request("/activity/", query_string="view=code&page=3")

        self.assertEqual(status, "200 OK")
        operations = load_recent_operations(self.repo_root)
        activity_operation = next(event for event in operations if event.operation_name == "GET /activity/")
        self.assertEqual(activity_operation.state, "completed")
        self.assertEqual(activity_operation.metadata["view"], "code")
        self.assertEqual(activity_operation.metadata["page"], "3")
        step_names = tuple(step.name for step in activity_operation.steps)
        self.assertIn("activity_load_events", step_names)
        self.assertIn("activity_render_event_cards", step_names)
        self.assertNotIn("activity_load_repository_state", step_names)

    def test_content_activity_request_still_records_repository_load_step(self) -> None:
        status, _, _ = self.request("/activity/", query_string="view=content")

        self.assertEqual(status, "200 OK")
        operations = load_recent_operations(self.repo_root)
        activity_operation = next(event for event in operations if event.operation_name == "GET /activity/")
        self.assertEqual(activity_operation.metadata["view"], "content")
        self.assertEqual(activity_operation.metadata["page"], "1")
        step_names = tuple(step.name for step in activity_operation.steps)
        self.assertIn("activity_load_repository_state", step_names)
        self.assertIn("activity_build_posts_index", step_names)

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

    def test_request_failure_is_recorded_as_failed_operation(self) -> None:
        with mock.patch("forum_web.web.render_instance_info_page", side_effect=RuntimeError("broken page")):
            status, _, body = self.request("/instance/")

        self.assertEqual(status, "500 Internal Server Error")
        self.assertIn("broken page", body)
        self.assertIn("<title>Server Error</title>", body)
        self.assertIn("</head>\n<body>\n", body)
        operations = load_recent_operations(self.repo_root)
        failed_operation = next(event for event in operations if event.operation_name == "GET /instance/")
        self.assertEqual(failed_operation.state, "failed")
        self.assertEqual(failed_operation.error_text, "broken page")

    def test_streamed_reindex_request_completes_operation_after_iterable_finishes(self) -> None:
        readiness = PostIndexReadiness(
            expected_post_count=1,
            indexed_post_count=0,
            indexed_head=None,
            current_head=self.run_command(["git", "-C", str(self.repo_root), "rev-parse", "HEAD"], cwd=self.repo_root).stdout.strip(),
            indexed_schema_version=None,
            count_mismatch=True,
            head_mismatch=True,
            schema_mismatch=True,
        )

        with mock.patch("forum_web.web.post_index_readiness", return_value=readiness):
            with mock.patch("forum_web.web.rebuild_post_index"):
                status, _, body = self.request("/")

        self.assertEqual(status, "200 OK")
        self.assertIn("Refreshing the forum", body)
        operations = load_recent_operations(self.repo_root)
        board_operation = next(event for event in operations if event.operation_name == "GET /")
        self.assertEqual(board_operation.state, "completed")

    def test_board_request_records_route_specific_timing_steps(self) -> None:
        status, _, _ = self.request("/")

        self.assertEqual(status, "200 OK")
        operations = load_recent_operations(self.repo_root)
        board_operation = next(event for event in operations if event.operation_name == "GET /")
        step_names = tuple(step.name for step in board_operation.steps)
        self.assertIn("board_load_repository_state", step_names)
        self.assertIn("board_build_page_context", step_names)
        self.assertIn("board_render_page", step_names)

    def test_compose_reply_request_records_route_specific_timing_steps(self) -> None:
        self.write_record(
            "records/posts/reply-001.txt",
            """
            Post-ID: reply-001
            Board-Tags: general
            Subject: Reply target
            Thread-ID: root-001
            Parent-ID: root-001

            Target reply body.
            """,
        )
        self.run_command(["git", "add", "."], cwd=self.repo_root)
        self.run_command(["git", "commit", "-m", "add reply target"], cwd=self.repo_root)
        ensure_post_index_current(self.repo_root).connection.close()

        status, _, _ = self.request(
            "/compose/reply",
            query_string="thread_id=root-001&parent_id=reply-001",
        )

        self.assertEqual(status, "200 OK")
        operations = load_recent_operations(self.repo_root)
        compose_reply_operation = next(event for event in operations if event.operation_name == "GET /compose/reply")
        step_names = tuple(step.name for step in compose_reply_operation.steps)
        self.assertIn("compose_reply_load_posts", step_names)
        self.assertIn("compose_reply_build_posts_index", step_names)
        self.assertIn("compose_reply_load_moderation_records", step_names)
        self.assertIn("compose_reply_derive_moderation_state", step_names)
        self.assertIn("compose_reply_load_identity_context", step_names)
        self.assertIn("compose_reply_lookup_thread", step_names)
        self.assertIn("compose_reply_lookup_parent_post", step_names)
        self.assertIn("compose_reply_render_page", step_names)

    def test_thread_request_records_route_specific_timing_steps(self) -> None:
        status, _, _ = self.request("/threads/root-001")

        self.assertEqual(status, "200 OK")
        operations = load_recent_operations(self.repo_root)
        thread_operation = next(event for event in operations if event.operation_name == "GET /threads/root-001")
        step_names = tuple(step.name for step in thread_operation.steps)
        self.assertIn("thread_load_repository_state", step_names)
        self.assertIn("thread_lookup_thread", step_names)
        self.assertIn("thread_render_page", step_names)

    def test_profile_request_records_route_specific_timing_steps(self) -> None:
        status, _, _ = self.request(f"/profiles/{identity_slug(self.identity_id)}")

        self.assertEqual(status, "200 OK")
        operations = load_recent_operations(self.repo_root)
        profile_operation = next(
            event for event in operations if event.operation_name == f"GET /profiles/{identity_slug(self.identity_id)}"
        )
        step_names = tuple(step.name for step in profile_operation.steps)
        self.assertIn("profile_load_repository_state", step_names)
        self.assertIn("profile_lookup_summary", step_names)
        self.assertIn("profile_render_page", step_names)


if __name__ == "__main__":
    unittest.main()
