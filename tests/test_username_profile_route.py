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

    def test_merged_profile_read_prefers_latest_single_claim_across_linked_identities(self) -> None:
        status, _, body = self.get("/profiles/openpgp-alpha")

        self.assertEqual(status, "200 OK")
        self.assertIn("Ilya Alt", body)
        self.assertIn("Ilya", body)
        self.assertIn("/user/ilya-alt", body)
        self.assertNotIn("/user/ilya</a>", body)
        self.assertNotIn("Profile View", body)
        self.assertNotIn("This profile view is derived", body)
        self.assertNotIn('class="breadcrumb"', body)

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

    def get(self, path: str, *, extra_env: dict[str, str] | None = None) -> tuple[str, dict[str, str], str]:
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

        env = {"FORUM_REPO_ROOT": str(self.repo_root)}
        if extra_env:
            env.update(extra_env)
        with mock.patch.dict(os.environ, env):
            body = b"".join(application(environ, start_response)).decode("utf-8")

        return response["status"], dict(response["headers"]), body

    def test_duplicate_username_route_resolves_to_canonical_root(self) -> None:
        status, _, body = self.get("/user/ilya")

        self.assertEqual(status, "200 OK")
        self.assertIn("openpgp:alpha", body)
        self.assertIn("Other Users With This Name", body)
        self.assertIn("/profiles/openpgp-beta", body)

    def test_identity_profile_lists_other_users_with_same_name(self) -> None:
        status, _, body = self.get("/profiles/openpgp-alpha")

        self.assertEqual(status, "200 OK")
        self.assertIn("Other Users With This Name", body)
        self.assertIn("/profiles/openpgp-beta", body)
        self.assertNotIn("linked identities", body)
        self.assertNotIn(">openpgp:beta</a>", body)
        self.assertIn("<details", body)
        self.assertIn(">Technical details<", body)
        self.assertNotIn("Key material", body)
        self.assertNotIn('id="profile-key-status"', body)
        self.assertNotIn('id="profile-private-key-output"', body)
        self.assertNotIn('id="profile-public-key-output"', body)
        self.assertNotIn('/assets/profile_key_viewer.js', body)

        other_users_index = body.index("Other Users With This Name")
        technical_details_index = body.rindex(">Technical details<")

        self.assertLess(other_users_index, technical_details_index)

    def test_non_root_duplicate_profile_offers_direct_merge_request(self) -> None:
        status, _, body = self.get("/profiles/openpgp-beta")

        self.assertEqual(status, "200 OK")
        self.assertNotIn("Likely Self-Merge", body)
        self.assertNotIn("not me", body)
        self.assertNotIn("/assets/profile_merge_suggestion.js", body)
        self.assertNotIn("/profiles/openpgp-beta/merge/action?action=request_merge", body)

    def test_non_root_duplicate_profile_offers_direct_merge_request_when_feature_enabled(self) -> None:
        status, _, body = self.get(
            "/profiles/openpgp-beta",
            extra_env={"FORUM_ENABLE_ACCOUNT_MERGE": "1"},
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("linked identities", body)
        self.assertIn("Likely Self-Merge", body)
        self.assertIn("not me", body)
        self.assertIn("/assets/profile_merge_suggestion.js", body)
        self.assertIn(
            "/profiles/openpgp-beta/merge/action?action=request_merge&other_identity_id=openpgp:alpha",
            body,
        )

    def test_revoked_merge_restores_other_users_section_on_canonical_root(self) -> None:
        self.write_record(
            "records/merge-requests/merge-request-001.txt",
            """
            Record-ID: merge-request-001
            Action: request_merge
            Requester-Identity-ID: openpgp:beta
            Target-Identity-ID: openpgp:alpha
            Actor-Identity-ID: openpgp:beta
            Timestamp: 2026-03-18T01:10:00Z

            please merge
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-002.txt",
            """
            Record-ID: merge-request-002
            Action: approve_merge
            Requester-Identity-ID: openpgp:beta
            Target-Identity-ID: openpgp:alpha
            Actor-Identity-ID: openpgp:alpha
            Timestamp: 2026-03-18T01:20:00Z

            approved
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-003.txt",
            """
            Record-ID: merge-request-003
            Action: revoke_merge
            Requester-Identity-ID: openpgp:beta
            Target-Identity-ID: openpgp:alpha
            Actor-Identity-ID: openpgp:beta
            Timestamp: 2026-03-18T01:30:00Z

            revoked
            """,
        )

        status, _, body = self.get("/user/ilya")

        self.assertEqual(status, "200 OK")
        self.assertIn("openpgp:alpha", body)
        self.assertIn("Other Users With This Name", body)
        self.assertIn("/profiles/openpgp-beta", body)

    def test_duplicate_username_list_collapses_after_first_five_peers(self) -> None:
        for index, identity_id in enumerate(
            (
                "openpgp:gamma",
                "openpgp:delta",
                "openpgp:epsilon",
                "openpgp:zeta",
                "openpgp:eta",
                "openpgp:theta",
            ),
            start=2,
        ):
            slug = identity_id.replace(":", "-")
            self.write_record(
                f"records/identity/identity-{slug}.txt",
                f"""
                Post-ID: identity-{slug}
                Board-Tags: identity
                Subject: identity bootstrap
                Identity-ID: {identity_id}
                Signer-Fingerprint: {index:016X}
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
                Timestamp: 2026-03-18T01:{index:02d}:00Z

                Ilya
                """,
            )

        status, _, body = self.get("/profiles/openpgp-alpha")

        self.assertEqual(status, "200 OK")
        self.assertIn("Other Users With This Name", body)
        self.assertIn("show 2 more", body)
        self.assertIn("/profiles/openpgp-beta", body)
        self.assertIn("/profiles/openpgp-gamma", body)


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

    def test_profile_signed_posts_uses_readable_labels_for_threads_and_replies(self) -> None:
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
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: Hello

            Root body.
            """,
        )
        self.write_record(
            "records/posts/reply-001.txt",
            """
            Post-ID: reply-001
            Board-Tags: general
            Thread-ID: root-001
            Parent-ID: root-001

            Reply first line.
            Reply second line.
            """,
        )
        self.write_record("records/posts/root-001.txt.pub.asc", self.alpha_public)
        self.write_record("records/posts/reply-001.txt.pub.asc", self.alpha_public)

        status, _, body = self.get(f"/profiles/{identity_slug(self.alpha_identity)}")

        self.assertEqual(status, "200 OK")
        self.assertIn('class="thread-chip thread-chip--thread" href="/posts/root-001">Hello</a>', body)
        self.assertNotIn('href="/posts/root-001">root-001</a>', body)
        self.assertIn('class="thread-chip thread-chip--reply" href="/posts/reply-001">Reply first line.</a>', body)
        self.assertNotIn('href="/posts/reply-001">reply-001</a>', body)

    def test_moderation_attribution_prefers_username_route_for_canonical_root(self) -> None:
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
        self.assertIn('/user/ilya', body)

    def test_post_attribution_falls_back_to_profile_after_revoked_merge(self) -> None:
        self.write_record(
            "records/profile-updates/profile-update-alpha.txt",
            f"""
            Record-ID: profile-update-alpha
            Action: set_display_name
            Source-Identity-ID: {self.alpha_identity}
            Timestamp: 2026-03-18T04:00:00Z

            Ilya
            """,
        )
        self.write_record(
            "records/profile-updates/profile-update-beta.txt",
            f"""
            Record-ID: profile-update-beta
            Action: set_display_name
            Source-Identity-ID: {self.beta_identity}
            Timestamp: 2026-03-18T04:10:00Z

            Ilya
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-010.txt",
            f"""
            Record-ID: merge-request-010
            Action: request_merge
            Requester-Identity-ID: {self.alpha_identity}
            Target-Identity-ID: {self.beta_identity}
            Actor-Identity-ID: {self.alpha_identity}
            Timestamp: 2026-03-18T04:20:00Z

            please merge
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-011.txt",
            f"""
            Record-ID: merge-request-011
            Action: approve_merge
            Requester-Identity-ID: {self.alpha_identity}
            Target-Identity-ID: {self.beta_identity}
            Actor-Identity-ID: {self.beta_identity}
            Timestamp: 2026-03-18T04:30:00Z

            approved
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-012.txt",
            f"""
            Record-ID: merge-request-012
            Action: revoke_merge
            Requester-Identity-ID: {self.alpha_identity}
            Target-Identity-ID: {self.beta_identity}
            Actor-Identity-ID: {self.alpha_identity}
            Timestamp: 2026-03-18T04:40:00Z

            revoked
            """,
        )
        self.write_record(
            "records/posts/root-002.txt",
            """
            Post-ID: root-002
            Board-Tags: general
            Subject: Split Hello

            Split body.
            """,
        )
        self.write_record("records/posts/root-002.txt.pub.asc", self.beta_public)

        status, _, body = self.get("/threads/root-002")

        self.assertEqual(status, "200 OK")
        self.assertIn(f'/profiles/{identity_slug(self.beta_identity)}', body)
        self.assertNotIn('/user/ilya', body)

    def test_moderation_attribution_falls_back_to_profile_after_revoked_merge(self) -> None:
        self.write_record(
            "records/profile-updates/profile-update-alpha.txt",
            f"""
            Record-ID: profile-update-alpha
            Action: set_display_name
            Source-Identity-ID: {self.alpha_identity}
            Timestamp: 2026-03-18T05:00:00Z

            Ilya
            """,
        )
        self.write_record(
            "records/profile-updates/profile-update-beta.txt",
            f"""
            Record-ID: profile-update-beta
            Action: set_display_name
            Source-Identity-ID: {self.beta_identity}
            Timestamp: 2026-03-18T05:10:00Z

            Ilya
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-020.txt",
            f"""
            Record-ID: merge-request-020
            Action: request_merge
            Requester-Identity-ID: {self.alpha_identity}
            Target-Identity-ID: {self.beta_identity}
            Actor-Identity-ID: {self.alpha_identity}
            Timestamp: 2026-03-18T05:20:00Z

            please merge
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-021.txt",
            f"""
            Record-ID: merge-request-021
            Action: approve_merge
            Requester-Identity-ID: {self.alpha_identity}
            Target-Identity-ID: {self.beta_identity}
            Actor-Identity-ID: {self.beta_identity}
            Timestamp: 2026-03-18T05:30:00Z

            approved
            """,
        )
        self.write_record(
            "records/merge-requests/merge-request-022.txt",
            f"""
            Record-ID: merge-request-022
            Action: revoke_merge
            Requester-Identity-ID: {self.alpha_identity}
            Target-Identity-ID: {self.beta_identity}
            Actor-Identity-ID: {self.alpha_identity}
            Timestamp: 2026-03-18T05:40:00Z

            revoked
            """,
        )
        self.write_record(
            "records/moderation/pin-root-001.txt",
            """
            Record-ID: pin-root-001
            Action: pin
            Target-Type: thread
            Target-ID: root-001
            Timestamp: 2026-03-18T05:50:00Z

            Pinning the thread.
            """,
        )
        self.write_record("records/moderation/pin-root-001.txt.pub.asc", self.beta_public)

        status, _, body = self.get("/activity/", "view=moderation")

        self.assertEqual(status, "200 OK")
        self.assertIn(f'/profiles/{identity_slug(self.beta_identity)}', body)
        self.assertNotIn('/user/ilya', body)


if __name__ == "__main__":
    unittest.main()
