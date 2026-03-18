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
from forum_web.web import application


class UsernameProfileRouteTests(unittest.TestCase):
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
            Bootstrap-By-Post: alpha-root
            Bootstrap-By-Thread: alpha-root

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
            Bootstrap-By-Post: beta-root
            Bootstrap-By-Thread: beta-root

            -----BEGIN PGP PUBLIC KEY BLOCK-----
            beta
            -----END PGP PUBLIC KEY BLOCK-----
            """,
        )
        self.write_record(
            "records/profile-updates/profile-update-alpha.txt",
            f"""
            Record-ID: profile-update-alpha
            Action: set_display_name
            Source-Identity-ID: {self.alpha}
            Timestamp: 2026-03-18T00:00:00Z

            Ilya
            """,
        )
        self.write_record(
            "records/profile-updates/profile-update-beta.txt",
            f"""
            Record-ID: profile-update-beta
            Action: set_display_name
            Source-Identity-ID: {self.beta}
            Timestamp: 2026-03-18T00:10:00Z

            Ilya Alt
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-001.txt",
            f"""
            Record-ID: merge-request-001
            Action: request_merge
            Requester-Identity-ID: {self.alpha}
            Target-Identity-ID: {self.beta}
            Actor-Identity-ID: {self.alpha}
            Timestamp: 2026-03-18T00:20:00Z

            please merge
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-002.txt",
            f"""
            Record-ID: merge-request-002
            Action: approve_merge
            Requester-Identity-ID: {self.alpha}
            Target-Identity-ID: {self.beta}
            Actor-Identity-ID: {self.beta}
            Timestamp: 2026-03-18T00:30:00Z

            approved
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

    def test_username_route_renders_joined_profile_and_visible_usernames(self) -> None:
        status, _, body = self.get("/user/ilya-alt")

        self.assertEqual(status, "200 OK")
        self.assertIn("Ilya Alt", body)
        self.assertIn("Ilya", body)
        self.assertIn("/user/ilya-alt", body)
        self.assertIn(self.alpha, body)

    def test_old_username_route_does_not_resolve_after_rename(self) -> None:
        status, _, _ = self.get("/user/ilya")

        self.assertEqual(status, "404 Not Found")


class UsernameProfileRouteCollisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        for identity_id, fingerprint in (
            ("openpgp:alpha", "AAAAAAAAAAAAAAAA"),
            ("openpgp:beta", "BBBBBBBBBBBBBBBB"),
        ):
            slug = identity_id.replace(":", "-")
            self.write_record(
                f"records/identity/identity-{slug}.txt",
                f"""
                Post-ID: identity-{slug}
                Board-Tags: identity
                Subject: identity bootstrap
                Identity-ID: {identity_id}
                Signer-Fingerprint: {fingerprint}
                Bootstrap-By-Post: root-{slug}
                Bootstrap-By-Thread: root-{slug}

                -----BEGIN PGP PUBLIC KEY BLOCK-----
                {slug}
                -----END PGP PUBLIC KEY BLOCK-----
                """,
            )
            self.write_record(
                f"records/profile-updates/profile-update-{slug}.txt",
                f"""
                Record-ID: profile-update-{slug}
                Action: set_display_name
                Source-Identity-ID: {identity_id}
                Timestamp: 2026-03-18T01:00:00Z

                Ilya
                """,
            )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_record(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")

    def get(self, path: str) -> tuple[str, dict[str, str], str]:
        environ = {
            "PATH_INFO": path,
            "QUERY_STRING": "",
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

    def test_ambiguous_username_route_returns_not_found(self) -> None:
        status, _, _ = self.get("/user/ilya")

        self.assertEqual(status, "404 Not Found")


class UsernameAttributionLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.openpgp_module_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()

        alpha = self.generate_signing_keypair("Alpha")
        beta = self.generate_signing_keypair("Beta")
        self.alpha_public = alpha["publicKey"]
        self.beta_public = beta["publicKey"]
        self.alpha_fingerprint = fingerprint_from_public_key_text(self.alpha_public)
        self.beta_fingerprint = fingerprint_from_public_key_text(self.beta_public)
        self.alpha_identity = build_identity_id(self.alpha_fingerprint)
        self.beta_identity = build_identity_id(self.beta_fingerprint)

        for identity_id, fingerprint, public_key_text, root_id in (
            (self.alpha_identity, self.alpha_fingerprint, self.alpha_public, "root-alpha"),
            (self.beta_identity, self.beta_fingerprint, self.beta_public, "root-beta"),
        ):
            record_id, payload = build_bootstrap_payload(
                identity_id=identity_id,
                signer_fingerprint=fingerprint,
                bootstrap_post_id=root_id,
                bootstrap_thread_id=root_id,
                public_key_text=public_key_text,
            )
            self.write_record(f"records/identity/{record_id}.txt", payload)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_node(self, script: str) -> str:
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", script],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
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
        return json.loads(self.run_node(script))

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

    def test_post_attribution_prefers_username_route_when_unambiguous(self) -> None:
        self.write_record(
            "records/profile-updates/profile-update-alpha.txt",
            f"""
            Record-ID: profile-update-alpha
            Action: set_display_name
            Source-Identity-ID: {self.alpha_identity}
            Timestamp: 2026-03-18T02:00:00Z

            Ilya
            """,
        )
        self.write_record(
            "records/profile-updates/profile-update-beta.txt",
            f"""
            Record-ID: profile-update-beta
            Action: set_display_name
            Source-Identity-ID: {self.beta_identity}
            Timestamp: 2026-03-18T02:10:00Z

            Ilya Alt
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-001.txt",
            f"""
            Record-ID: merge-request-001
            Action: request_merge
            Requester-Identity-ID: {self.alpha_identity}
            Target-Identity-ID: {self.beta_identity}
            Actor-Identity-ID: {self.alpha_identity}
            Timestamp: 2026-03-18T02:20:00Z

            please merge
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-002.txt",
            f"""
            Record-ID: merge-request-002
            Action: approve_merge
            Requester-Identity-ID: {self.alpha_identity}
            Target-Identity-ID: {self.beta_identity}
            Actor-Identity-ID: {self.beta_identity}
            Timestamp: 2026-03-18T02:30:00Z

            approved
            """,
        )
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: Hello

            Root body.
            """,
        )
        self.write_record("records/posts/root-001.txt.pub.asc", self.alpha_public)

        status, _, body = self.get("/threads/root-001")

        self.assertEqual(status, "200 OK")
        self.assertIn('/user/ilya-alt', body)
        self.assertNotIn(f'/profiles/{identity_slug(self.alpha_identity)}', body)

    def test_moderation_attribution_falls_back_to_identity_route_when_username_is_ambiguous(self) -> None:
        self.write_record(
            "records/profile-updates/profile-update-alpha.txt",
            f"""
            Record-ID: profile-update-alpha
            Action: set_display_name
            Source-Identity-ID: {self.alpha_identity}
            Timestamp: 2026-03-18T03:00:00Z

            Ilya
            """,
        )
        self.write_record(
            "records/profile-updates/profile-update-beta.txt",
            f"""
            Record-ID: profile-update-beta
            Action: set_display_name
            Source-Identity-ID: {self.beta_identity}
            Timestamp: 2026-03-18T03:10:00Z

            Ilya
            """,
        )
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: Hello

            Root body.
            """,
        )
        self.write_record(
            "records/moderation/pin-root-001.txt",
            """
            Record-ID: pin-root-001
            Action: pin
            Target-Type: thread
            Target-ID: root-001
            Timestamp: 2026-03-18T03:20:00Z

            Pinning the thread.
            """,
        )
        self.write_record("records/moderation/pin-root-001.txt.pub.asc", self.alpha_public)

        status, _, body = self.get("/activity/", "view=moderation")

        self.assertEqual(status, "200 OK")
        self.assertIn(f'/profiles/{identity_slug(self.alpha_identity)}', body)
        self.assertNotIn('/user/ilya', body)


if __name__ == "__main__":
    unittest.main()
