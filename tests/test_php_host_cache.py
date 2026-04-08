from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from forum_core.identity import build_identity_id, fingerprint_from_public_key_text, identity_slug
from forum_core.php_native_reads import (
    rebuild_php_native_compose_reply_snapshots,
    rebuild_php_native_profile_snapshots,
    rebuild_php_native_thread_snapshots,
    thread_snapshot_db_path,
)


class PhpHostCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.index_path = self.repo_root / "php_host" / "public" / "index.php"
        self.config_path = self.repo_root / "php_host" / "public" / "forum_host_config.php"
        self.original_config = self.config_path.read_text(encoding="utf-8") if self.config_path.exists() else None
        self.openpgp_module_url = (
            self.repo_root / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        self.repo_tempdir = tempfile.TemporaryDirectory()
        self.cache_tempdir = tempfile.TemporaryDirectory()
        self.static_tempdir = tempfile.TemporaryDirectory()
        self.data_repo_root = Path(self.repo_tempdir.name)
        (self.data_repo_root / "records" / "posts").mkdir(parents=True, exist_ok=True)

        self.run_command(["git", "init"], cwd=self.data_repo_root)
        self.run_command(["git", "config", "user.name", "Codex Test"], cwd=self.data_repo_root)
        self.run_command(["git", "config", "user.email", "codex@example.com"], cwd=self.data_repo_root)

        self.user_keys = self.generate_signing_keypair("PHP Host Cache Test")
        self.write_php_host_config()

    def tearDown(self) -> None:
        if self.original_config is None:
            self.config_path.unlink(missing_ok=True)
        else:
            self.config_path.write_text(self.original_config, encoding="utf-8")
        self.static_tempdir.cleanup()
        self.cache_tempdir.cleanup()
        self.repo_tempdir.cleanup()

    def write_php_host_config(self) -> None:
        self.config_path.write_text(
            "\n".join(
                [
                    "<?php",
                    "",
                    "declare(strict_types=1);",
                    "",
                    "return [",
                    f"    'app_root' => {self.repo_root.as_posix()!r},",
                    f"    'repo_root' => {self.data_repo_root.as_posix()!r},",
                    f"    'cache_dir' => {(Path(self.cache_tempdir.name) / 'cache').as_posix()!r},",
                    f"    'static_html_dir' => {(Path(self.static_tempdir.name) / '_static_html').as_posix()!r},",
                    "    'site_title' => 'Forum Reader',",
                    "    'microcache_ttl' => 5,",
                    "];",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def run_command(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        input_bytes: bytes | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
        if input_bytes is None:
            return subprocess.run(
                command,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
        return subprocess.run(
            command,
            cwd=cwd,
            input=input_bytes,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
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

    def php_request(
        self,
        path: str,
        *,
        method: str = "GET",
        query_string: str = "",
        body: bytes = b"",
        content_type: str = "",
        cookie: str = "",
    ) -> dict[str, object]:
        env = os.environ.copy()
        env.update(
            {
                "FORUM_ENABLE_FIRST_POST_POW": "0",
                "FORUM_ENABLE_THREAD_AUTO_REPLY": "0",
                "GATEWAY_INTERFACE": "CGI/1.1",
                "REDIRECT_STATUS": "200",
                "REQUEST_METHOD": method,
                "REQUEST_URI": path if not query_string else path + "?" + query_string,
                "QUERY_STRING": query_string,
                "SERVER_NAME": "localhost",
                "SERVER_PORT": "80",
                "SERVER_PROTOCOL": "HTTP/1.1",
                "SCRIPT_FILENAME": str(self.index_path),
                "SCRIPT_NAME": "/index.php",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": str(len(body)),
            }
        )
        if cookie:
            env["HTTP_COOKIE"] = cookie
        result = self.run_command(
            ["php-cgi", "-q", str(self.index_path)],
            input_bytes=body,
            env=env,
        )
        stdout = result.stdout.decode("utf-8") if isinstance(result.stdout, bytes) else result.stdout
        raw_headers, response_body = stdout.split("\r\n\r\n", 1)
        header_lines = [line for line in raw_headers.split("\r\n") if line]
        status_line = next((line for line in header_lines if line.startswith("Status: ")), "Status: 200 OK")
        status_code = int(status_line.split(" ", 2)[1])
        return {
            "status": status_code,
            "headers": [line for line in header_lines if not line.startswith("Status: ")],
            "body": response_body,
        }

    def build_thread_payload(self, *, post_id: str, subject: str, body_text: str) -> str:
        return dedent(
            f"""
            Post-ID: {post_id}
            Board-Tags: general
            Subject: {subject}

            {body_text}
            """
        ).lstrip()

    def build_create_thread_body(self, payload_text: str) -> bytes:
        return json.dumps(
            {
                "payload": payload_text,
                "signature": self.sign_payload(payload_text),
                "public_key": self.user_keys["publicKey"],
                "dry_run": False,
            }
        ).encode("utf-8")

    def profile_slug(self) -> str:
        fingerprint = fingerprint_from_public_key_text(self.user_keys["publicKey"])
        return identity_slug(build_identity_id(fingerprint))

    def cache_files(self) -> list[Path]:
        cache_root = Path(self.cache_tempdir.name) / "cache"
        if not cache_root.exists():
            return []
        return sorted(path for path in cache_root.glob("*.cgi"))

    def static_html_files(self) -> list[Path]:
        static_root = Path(self.static_tempdir.name) / "_static_html"
        if not static_root.exists():
            return []
        return sorted(path for path in static_root.rglob("index.html"))

    def php_cache_helper(self, body: str, *, path: str = "/", query_string: str = "", method: str = "GET", cookie: str = "") -> str:
        cache_path = (self.repo_root / "php_host" / "public" / "cache.php").as_posix()
        static_html_root = (Path(self.static_tempdir.name) / "_static_html").as_posix()
        script = dedent(
            f"""
            $_SERVER['REQUEST_METHOD'] = {method!r};
            $_SERVER['REQUEST_URI'] = {path if not query_string else path + "?" + query_string!r};
            $_SERVER['QUERY_STRING'] = {query_string!r};
            if ({cookie!r} !== '') {{
                $_SERVER['HTTP_COOKIE'] = {cookie!r};
            }}

            function forum_host_config(): array {{
                return ['static_html_dir' => {static_html_root!r}];
            }}

            function forum_public_dir(): string {{
                return {str((self.repo_root / "php_host" / "public").as_posix())!r};
            }}

            require {cache_path!r};

            {body}
            """
        ).strip()
        result = self.run_command(["php", "-r", script])
        return result.stdout

    def write_committed_post(self, *, post_id: str, subject: str, body_text: str) -> None:
        relative_path = Path("records") / "posts" / f"{post_id}.txt"
        payload = self.build_thread_payload(post_id=post_id, subject=subject, body_text=body_text)
        (self.data_repo_root / relative_path).write_text(payload, encoding="utf-8")
        self.run_command(["git", "add", relative_path.as_posix()], cwd=self.data_repo_root)
        self.run_command(["git", "commit", "-m", f"Add {post_id}"], cwd=self.data_repo_root)

    def write_php_native_board_index_snapshot(self, payload: dict[str, object]) -> Path:
        snapshot_path = (
            self.data_repo_root
            / "state"
            / "cache"
            / "php_native_reads"
            / "board_index_root.json"
        )
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return snapshot_path

    def write_static_thread_html(self, thread_id: str, html_text: str) -> Path:
        static_path = (
            Path(self.static_tempdir.name)
            / "_static_html"
            / "threads"
            / thread_id
            / "index.html"
        )
        static_path.parent.mkdir(parents=True, exist_ok=True)
        static_path.write_text(html_text, encoding="utf-8")
        return static_path

    def php_native_counter_value(self, route_path: str, user_type: str, outcome: str) -> int:
        db_path = thread_snapshot_db_path(self.data_repo_root)
        if not db_path.exists():
            return 0
        connection = sqlite3.connect(db_path)
        try:
            row = connection.execute(
                "SELECT count FROM php_native_read_counters WHERE route_path = ? AND user_type = ? AND outcome = ?",
                (route_path, user_type, outcome),
            ).fetchone()
        finally:
            connection.close()
        return 0 if row is None else int(row[0])

    def test_php_host_caches_allowlisted_reads_and_marks_hit_headers(self) -> None:
        first = self.php_request("/api/list_index")
        second = self.php_request("/api/list_index")

        self.assertEqual(first["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", first["headers"])
        self.assertIn("X-Forum-Response-Source: cgi", first["headers"])
        self.assertTrue(any(header.startswith("X-Forum-Request-Duration-Ms: ") for header in first["headers"]))
        self.assertTrue(any(header.startswith("X-Forum-Cgi-Duration-Ms: ") for header in first["headers"]))
        self.assertTrue(any(header.startswith("X-Forum-Operation-Id: ") for header in first["headers"]))
        self.assertEqual(second["status"], 200)
        self.assertIn("X-Forum-Php-Cache: HIT", second["headers"])
        self.assertIn("X-Forum-Response-Source: php-microcache", second["headers"])
        self.assertTrue(any(header.startswith("X-Forum-Request-Duration-Ms: ") for header in second["headers"]))
        self.assertEqual(first["body"], second["body"])
        self.assertEqual(len(self.cache_files()), 1)

    def test_php_host_stores_and_reuses_static_html_for_allowlisted_reads(self) -> None:
        self.write_committed_post(
            post_id="thread-php-static-001",
            subject="Hello static HTML",
            body_text="This thread should create a static artifact.",
        )

        first = self.php_request("/threads/thread-php-static-001")

        self.assertEqual(first["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", first["headers"])
        self.assertIn("Refreshing the forum...", first["body"])

        rebuild = self.php_request("/threads/thread-php-static-001", query_string="__forum_rebuild=1")

        self.assertEqual(rebuild["status"], 200)
        self.assertIn("Hello static HTML", rebuild["body"])

        materialized = self.php_request("/threads/thread-php-static-001")

        self.assertEqual(materialized["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", materialized["headers"])
        self.assertIn("Hello static HTML", materialized["body"])
        self.assertEqual(
            self.static_html_files(),
            [Path(self.static_tempdir.name) / "_static_html" / "threads" / "thread-php-static-001" / "index.html"],
        )

        second = self.php_request("/threads/thread-php-static-001")

        self.assertEqual(second["status"], 200)
        self.assertIn("X-Forum-Static-Html: HIT", second["headers"])
        self.assertIn("X-Forum-Response-Source: static-html", second["headers"])
        self.assertTrue(any(header.startswith("X-Forum-Request-Duration-Ms: ") for header in second["headers"]))
        self.assertIn("Hello static HTML", second["body"])

    def test_php_host_sets_asset_cache_headers_without_microcaching_assets(self) -> None:
        response = self.php_request("/assets/site.css")

        self.assertEqual(response["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", response["headers"])
        self.assertIn("Cache-Control: public, max-age=3600", response["headers"])
        self.assertEqual(self.cache_files(), [])

    def test_php_host_serves_copy_field_asset_as_javascript(self) -> None:
        response = self.php_request("/assets/copy_field.js")

        self.assertEqual(response["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", response["headers"])
        self.assertIn("Cache-Control: public, max-age=3600", response["headers"])
        self.assertIn("Content-Type: text/javascript; charset=utf-8", response["headers"])
        self.assertIn('document.addEventListener("click"', response["body"])
        self.assertEqual(self.cache_files(), [])

    def test_php_host_serves_primary_nav_asset_as_javascript(self) -> None:
        response = self.php_request("/assets/primary_nav.js")

        self.assertEqual(response["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", response["headers"])
        self.assertIn("Cache-Control: public, max-age=3600", response["headers"])
        self.assertIn("Content-Type: text/javascript; charset=utf-8", response["headers"])
        self.assertIn("export function enhancePrimaryNav", response["body"])
        self.assertEqual(self.cache_files(), [])

    def test_php_host_renders_primary_nav_hooks_and_script(self) -> None:
        response = self.php_request("/")

        self.assertEqual(response["status"], 200)
        self.assertIn('<nav class="site-header-nav" data-primary-nav aria-label="Primary">', response["body"])
        self.assertIn('<a data-primary-nav-link href="/" aria-current="page">Home</a>', response["body"])
        self.assertIn('data-profile-nav-link', response["body"])
        self.assertIn('<script type="module" src="/assets/primary_nav.js"></script>', response["body"])

    def test_static_html_request_only_allows_safe_anonymous_html_routes(self) -> None:
        self.assertEqual(
            self.php_cache_helper("echo forum_static_html_request() ? 'yes' : 'no';", path="/threads/example-thread"),
            "yes",
        )
        self.assertEqual(
            self.php_cache_helper("echo forum_static_html_request() ? 'yes' : 'no';", path="/api/get_thread"),
            "no",
        )
        self.assertEqual(
            self.php_cache_helper("echo forum_static_html_request() ? 'yes' : 'no';", path="/profiles/example/update"),
            "no",
        )
        self.assertEqual(
            self.php_cache_helper("echo forum_static_html_request() ? 'yes' : 'no';", path="/threads/example-thread", query_string="page=2"),
            "no",
        )
        self.assertEqual(
            self.php_cache_helper(
                "echo forum_static_html_request() ? 'yes' : 'no';",
                path="/threads/example-thread",
                cookie="forum_identity_hint=test",
            ),
            "yes",
        )
        self.assertEqual(
            self.php_cache_helper(
                "echo forum_static_html_request() ? 'yes' : 'no';",
                path="/instance/",
                cookie="forum_identity_hint=test",
            ),
            "yes",
        )
        self.assertEqual(
            self.php_cache_helper(
                "echo forum_static_html_request() ? 'yes' : 'no';",
                path="/",
                cookie="forum_identity_hint=test",
            ),
            "yes",
        )
        self.assertEqual(
            self.php_cache_helper(
                "putenv('FORUM_ENABLE_USERNAME_CLAIM_CTA=0'); echo forum_static_html_request() ? 'yes' : 'no';",
                path="/compose/thread",
                cookie="forum_identity_hint=test",
            ),
            "yes",
        )
        self.assertEqual(
            self.php_cache_helper(
                "putenv('FORUM_ENABLE_USERNAME_CLAIM_CTA='); echo forum_static_html_request() ? 'yes' : 'no';",
                path="/compose/thread",
                cookie="forum_identity_hint=test",
            ),
            "no",
        )
        self.assertEqual(
            self.php_cache_helper(
                "putenv('FORUM_ENABLE_USERNAME_CLAIM_CTA=0'); echo forum_static_html_request() ? 'yes' : 'no';",
                path="/activity/",
                cookie="forum_identity_hint=test",
            ),
            "yes",
        )
        self.assertEqual(
            self.php_cache_helper(
                "putenv('FORUM_ENABLE_USERNAME_CLAIM_CTA=0'); echo forum_static_html_request() ? 'yes' : 'no';",
                path="/activity/",
                query_string="view=code",
                cookie="forum_identity_hint=test",
            ),
            "no",
        )

    def test_static_html_public_path_maps_allowlisted_routes_to_index_files(self) -> None:
        expected_root = (Path(self.static_tempdir.name) / "_static_html").as_posix()
        self.assertEqual(
            self.php_cache_helper("echo forum_static_html_public_path('/');"),
            f"{expected_root}/index.html",
        )
        self.assertEqual(
            self.php_cache_helper("echo forum_static_html_public_path('/threads/example-thread');"),
            f"{expected_root}/threads/example-thread/index.html",
        )
        self.assertEqual(
            self.php_cache_helper("echo forum_static_html_public_path('/profiles/example-user/');"),
            f"{expected_root}/profiles/example-user/index.html",
        )
        self.assertEqual(
            self.php_cache_helper("var_export(forum_static_html_public_path('/profiles/example-user/update'));"),
            "NULL",
        )

    def test_successful_write_clears_php_microcache(self) -> None:
        warm = self.php_request("/")
        self.assertIn("X-Forum-Php-Cache: MISS", warm["headers"])
        self.assertEqual(len(self.cache_files()), 1)
        self.assertEqual(len(self.static_html_files()), 1)

        payload_text = self.build_thread_payload(
            post_id="thread-php-cache-001",
            subject="Cache invalidation",
            body_text="This write should clear the PHP host cache.",
        )
        write_response = self.php_request(
            "/api/create_thread",
            method="POST",
            body=self.build_create_thread_body(payload_text),
            content_type="application/json",
        )

        self.assertEqual(write_response["status"], 200)
        self.assertIn("Record-ID: thread-php-cache-001", write_response["body"])
        self.assertEqual(self.cache_files(), [])
        self.assertEqual(self.static_html_files(), [])

        refreshed = self.php_request("/")
        self.assertIn("X-Forum-Php-Native: HIT", refreshed["headers"])
        self.assertIn("thread-php-cache-001", refreshed["body"])
        self.assertEqual(self.cache_files(), [])

    def test_php_host_shows_status_page_before_blocking_rebuild_request(self) -> None:
        self.write_committed_post(
            post_id="thread-php-reindex-001",
            subject="Hello",
            body_text="This committed post should trigger a cold-start rebuild.",
        )

        status_page = self.php_request("/")

        self.assertEqual(status_page["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", status_page["headers"])
        self.assertIn("Refreshing the forum...", status_page["body"])
        self.assertIn("A small interval of stillness while the next page arrives.", status_page["body"])
        self.assertIn("__forum_rebuild=1", status_page["body"])
        self.assertIn('<main class="wrap">\n    <section class="card">', status_page["body"])
        self.assertIn('</main>\n  <iframe id="forum-reindex-worker"', status_page["body"])
        self.assertEqual(self.cache_files(), [])

        rebuild_response = self.php_request("/", query_string="__forum_rebuild=1")

        self.assertEqual(rebuild_response["status"], 200)
        self.assertIn("Hello", rebuild_response["body"])
        self.assertNotIn("Refreshing the forum...", rebuild_response["body"])
        self.assertEqual(self.cache_files(), [])

        final_response = self.php_request("/")
        self.assertEqual(final_response["status"], 200)
        self.assertIn("Hello", final_response["body"])
        self.assertNotIn("Refreshing the forum...", final_response["body"])
        self.assertEqual(len(self.cache_files()), 1)

    def test_root_can_render_from_php_native_snapshot_without_python_bridge(self) -> None:
        self.write_php_native_board_index_snapshot(
            {
                "route": "/",
                "thread_rows": [
                    {
                        "post_id": "root-native-001",
                        "thread_href": "/threads/root-native-001",
                        "subject": "Native root thread",
                        "preview": "Native preview line.",
                        "tags": ["meta"],
                        "reply_count": 2,
                        "thread_type": "task",
                        "last_activity_at": "2026-03-17T12:00:00Z",
                    }
                ],
                "stats": {
                    "post_count": 3,
                    "thread_count": 1,
                    "board_tag_count": 1,
                },
            }
        )
        self.config_path.write_text(
            "\n".join(
                [
                    "<?php",
                    "",
                    "declare(strict_types=1);",
                    "",
                    "return [",
                    "    'app_root' => '/definitely/missing-app-root',",
                    f"    'repo_root' => {self.data_repo_root.as_posix()!r},",
                    f"    'cache_dir' => {(Path(self.cache_tempdir.name) / 'cache').as_posix()!r},",
                    f"    'static_html_dir' => {(Path(self.static_tempdir.name) / '_static_html').as_posix()!r},",
                    "    'site_title' => 'zenmemes',",
                    "    'microcache_ttl' => 5,",
                    "];",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        response = self.php_request("/")

        self.assertEqual(response["status"], 200)
        self.assertIn("X-Forum-Php-Native: HIT", response["headers"])
        self.assertIn("/threads/root-native-001", response["body"])
        self.assertIn("Native root thread", response["body"])
        self.assertIn("Native preview line.", response["body"])
        self.assertIn("[meta]", response["body"])
        self.assertIn("2 replies", response["body"])
        self.assertIn("task", response["body"])
        self.assertIn('class="friendly-timestamp"', response["body"])
        self.assertIn('title="March 17, 2026 · 12:00:00 UTC"', response["body"])
        self.assertIn("<title>zenmemes</title>", response["body"])
        self.assertIn('class="site-header-title"><a href="/">zenmemes</a>', response["body"])
        self.assertEqual(response["body"].count('aria-current="page"'), 1)
        self.assertIn('<a data-primary-nav-link href="/" aria-current="page">Home</a>', response["body"])
        self.assertIn("posts loaded", response["body"])
        self.assertIn('href="/?format=rss"', response["body"])

    def test_query_bearing_root_request_does_not_use_php_native_snapshot(self) -> None:
        self.write_php_native_board_index_snapshot(
            {
                "route": "/",
                "thread_rows": [],
                "stats": {
                    "post_count": 0,
                    "thread_count": 0,
                    "board_tag_count": 0,
                },
            }
        )
        self.config_path.write_text(
            "\n".join(
                [
                    "<?php",
                    "",
                    "declare(strict_types=1);",
                    "",
                    "return [",
                    "    'app_root' => '/definitely/missing-app-root',",
                    f"    'repo_root' => {self.data_repo_root.as_posix()!r},",
                    f"    'cache_dir' => {(Path(self.cache_tempdir.name) / 'cache').as_posix()!r},",
                    f"    'static_html_dir' => {(Path(self.static_tempdir.name) / '_static_html').as_posix()!r},",
                    "    'site_title' => 'zenmemes',",
                    "    'microcache_ttl' => 5,",
                    "];",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        response = self.php_request("/", query_string="board_tag=meta")

        self.assertEqual(response["status"], 500)
        self.assertNotIn("X-Forum-Php-Native: HIT", response["headers"])
        self.assertIn("Forum CGI bridge failed.", response["body"])

    def test_root_can_render_from_php_native_snapshot_with_identity_hint_cookie(self) -> None:
        self.write_php_native_board_index_snapshot(
            {
                "route": "/",
                "thread_rows": [
                    {
                        "post_id": "root-native-cookie-001",
                        "thread_href": "/threads/root-native-cookie-001",
                        "subject": "Native cookie-safe root",
                        "preview": "Cookie-safe preview.",
                        "tags": [],
                        "reply_count": 0,
                        "thread_type": None,
                        "last_activity_at": "2026-03-17T12:00:00Z",
                    }
                ],
                "stats": {
                    "post_count": 1,
                    "thread_count": 1,
                    "board_tag_count": 0,
                },
            }
        )
        self.config_path.write_text(
            "\n".join(
                [
                    "<?php",
                    "",
                    "declare(strict_types=1);",
                    "",
                    "return [",
                    "    'app_root' => '/definitely/missing-app-root',",
                    f"    'repo_root' => {self.data_repo_root.as_posix()!r},",
                    f"    'cache_dir' => {(Path(self.cache_tempdir.name) / 'cache').as_posix()!r},",
                    f"    'static_html_dir' => {(Path(self.static_tempdir.name) / '_static_html').as_posix()!r},",
                    "    'site_title' => 'zenmemes',",
                    "    'microcache_ttl' => 5,",
                    "];",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        response = self.php_request("/", cookie="forum_identity_hint=test")

        self.assertEqual(response["status"], 200)
        self.assertIn("X-Forum-Php-Native: HIT", response["headers"])
        self.assertIn("Native cookie-safe root", response["body"])

    def test_root_with_unexpected_cookie_bypasses_php_native_snapshot(self) -> None:
        self.write_php_native_board_index_snapshot(
            {
                "route": "/",
                "thread_rows": [],
                "stats": {
                    "post_count": 0,
                    "thread_count": 0,
                    "board_tag_count": 0,
                },
            }
        )
        self.config_path.write_text(
            "\n".join(
                [
                    "<?php",
                    "",
                    "declare(strict_types=1);",
                    "",
                    "return [",
                    "    'app_root' => '/definitely/missing-app-root',",
                    f"    'repo_root' => {self.data_repo_root.as_posix()!r},",
                    f"    'cache_dir' => {(Path(self.cache_tempdir.name) / 'cache').as_posix()!r},",
                    f"    'static_html_dir' => {(Path(self.static_tempdir.name) / '_static_html').as_posix()!r},",
                    "    'site_title' => 'zenmemes',",
                    "    'microcache_ttl' => 5,",
                    "];",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        response = self.php_request("/", cookie="session=abc")

        self.assertEqual(response["status"], 500)
        self.assertNotIn("X-Forum-Php-Native: HIT", response["headers"])
        self.assertIn("Forum CGI bridge failed.", response["body"])

    def test_thread_route_can_render_from_php_native_sqlite_snapshot(self) -> None:
        payload = self.build_thread_payload(
            post_id="thread-native-001",
            subject="Native thread",
            body_text="Root body for native thread.",
        )
        response = self.php_request(
            "/api/create_thread",
            method="POST",
            body=self.build_create_thread_body(payload),
            content_type="application/json",
        )
        self.assertEqual(response["status"], 200)

        rebuild_php_native_thread_snapshots(self.data_repo_root)

        thread_response = self.php_request("/threads/thread-native-001")

        self.assertEqual(thread_response["status"], 200)
        self.assertIn("X-Forum-Php-Native: HIT", thread_response["headers"])
        self.assertNotIn('aria-current="page"', thread_response["body"])
        self.assertIn("Native thread", thread_response["body"])
        self.assertIn("compose a reply", thread_response["body"])
        self.assertIn("change title", thread_response["body"])
        self.assertEqual(
            self.php_native_counter_value("/threads/thread-native-001", "anonymous", "native_hit"),
            1,
        )

    def test_thread_route_can_render_from_php_native_snapshot_with_identity_hint_cookie(self) -> None:
        payload = self.build_thread_payload(
            post_id="thread-native-cookie-001",
            subject="Native thread cookie-safe",
            body_text="Root body for native cookie-safe thread.",
        )
        response = self.php_request(
            "/api/create_thread",
            method="POST",
            body=self.build_create_thread_body(payload),
            content_type="application/json",
        )
        self.assertEqual(response["status"], 200)

        rebuild_php_native_thread_snapshots(self.data_repo_root)

        thread_response = self.php_request("/threads/thread-native-cookie-001", cookie="forum_identity_hint=test")

        self.assertEqual(thread_response["status"], 200)
        self.assertIn("X-Forum-Php-Native: HIT", thread_response["headers"])
        self.assertIn("Native thread cookie-safe", thread_response["body"])

    def test_thread_route_with_unexpected_cookie_bypasses_php_native_snapshot(self) -> None:
        payload = self.build_thread_payload(
            post_id="thread-native-unexpected-cookie-001",
            subject="Unexpected cookie fallback",
            body_text="Root body for unexpected cookie fallback.",
        )
        response = self.php_request(
            "/api/create_thread",
            method="POST",
            body=self.build_create_thread_body(payload),
            content_type="application/json",
        )
        self.assertEqual(response["status"], 200)

        rebuild_php_native_thread_snapshots(self.data_repo_root)

        thread_response = self.php_request("/threads/thread-native-unexpected-cookie-001", cookie="session=abc")

        self.assertEqual(thread_response["status"], 200)
        self.assertNotIn("X-Forum-Php-Native: HIT", thread_response["headers"])
        self.assertIn("Unexpected cookie fallback", thread_response["body"])

    def test_compose_reply_route_can_render_from_php_native_snapshot(self) -> None:
        payload = self.build_thread_payload(
            post_id="thread-compose-native-001",
            subject="Compose reply native thread",
            body_text="Root body for compose reply native thread.",
        )
        response = self.php_request(
            "/api/create_thread",
            method="POST",
            body=self.build_create_thread_body(payload),
            content_type="application/json",
        )
        self.assertEqual(response["status"], 200)
        reply_payload = dedent(
            """
            Post-ID: reply-compose-native-001
            Board-Tags: general
            Subject: Compose reply native target
            Thread-ID: thread-compose-native-001
            Parent-ID: thread-compose-native-001

            Reply body for native compose reply.
            """
        ).lstrip()
        (self.data_repo_root / "records" / "posts" / "reply-compose-native-001.txt").write_text(reply_payload, encoding="utf-8")
        self.run_command(["git", "add", "records/posts/reply-compose-native-001.txt"], cwd=self.data_repo_root)
        self.run_command(["git", "commit", "-m", "Add compose reply target"], cwd=self.data_repo_root)

        rebuild_php_native_compose_reply_snapshots(self.data_repo_root)

        compose_response = self.php_request(
            "/compose/reply",
            query_string="thread_id=thread-compose-native-001&parent_id=reply-compose-native-001",
        )

        self.assertEqual(compose_response["status"], 200)
        self.assertIn("X-Forum-Php-Native: HIT", compose_response["headers"])
        self.assertIn("X-Forum-Response-Source: php-native-compose-reply", compose_response["headers"])
        self.assertIn("Compose a signed reply", compose_response["body"])
        self.assertIn("Replying to", compose_response["body"])
        self.assertIn("Reply body for native compose reply.", compose_response["body"])
        self.assertEqual(
            self.php_native_counter_value(
                "/compose/reply?thread_id=thread-compose-native-001&parent_id=reply-compose-native-001",
                "anonymous",
                "native_hit",
            ),
            1,
        )

    def test_compose_reply_route_can_render_from_php_native_snapshot_with_identity_hint_cookie(self) -> None:
        payload = self.build_thread_payload(
            post_id="thread-compose-cookie-001",
            subject="Compose reply cookie-safe thread",
            body_text="Root body for compose reply cookie-safe thread.",
        )
        response = self.php_request(
            "/api/create_thread",
            method="POST",
            body=self.build_create_thread_body(payload),
            content_type="application/json",
        )
        self.assertEqual(response["status"], 200)
        reply_payload = dedent(
            """
            Post-ID: reply-compose-cookie-001
            Board-Tags: general
            Subject: Compose reply cookie-safe target
            Thread-ID: thread-compose-cookie-001
            Parent-ID: thread-compose-cookie-001

            Reply body for cookie-safe compose reply.
            """
        ).lstrip()
        (self.data_repo_root / "records" / "posts" / "reply-compose-cookie-001.txt").write_text(reply_payload, encoding="utf-8")
        self.run_command(["git", "add", "records/posts/reply-compose-cookie-001.txt"], cwd=self.data_repo_root)
        self.run_command(["git", "commit", "-m", "Add cookie-safe compose reply target"], cwd=self.data_repo_root)

        rebuild_php_native_compose_reply_snapshots(self.data_repo_root)

        compose_response = self.php_request(
            "/compose/reply",
            query_string="thread_id=thread-compose-cookie-001&parent_id=reply-compose-cookie-001",
            cookie="forum_identity_hint=test",
        )

        self.assertEqual(compose_response["status"], 200)
        self.assertIn("X-Forum-Php-Native: HIT", compose_response["headers"])
        self.assertIn("Reply body for cookie-safe compose reply.", compose_response["body"])

    def test_compose_reply_snapshot_miss_falls_through_and_is_counted(self) -> None:
        payload = self.build_thread_payload(
            post_id="thread-compose-fallback-001",
            subject="Compose reply fallback thread",
            body_text="Root body for compose reply fallback thread.",
        )
        response = self.php_request(
            "/api/create_thread",
            method="POST",
            body=self.build_create_thread_body(payload),
            content_type="application/json",
        )
        self.assertEqual(response["status"], 200)
        reply_payload = dedent(
            """
            Post-ID: reply-compose-fallback-001
            Board-Tags: general
            Subject: Compose reply fallback target
            Thread-ID: thread-compose-fallback-001
            Parent-ID: thread-compose-fallback-001

            Reply body for fallback compose reply.
            """
        ).lstrip()
        (self.data_repo_root / "records" / "posts" / "reply-compose-fallback-001.txt").write_text(reply_payload, encoding="utf-8")
        self.run_command(["git", "add", "records/posts/reply-compose-fallback-001.txt"], cwd=self.data_repo_root)
        self.run_command(["git", "commit", "-m", "Add fallback compose reply target"], cwd=self.data_repo_root)

        rebuild_php_native_compose_reply_snapshots(self.data_repo_root)
        db_path = thread_snapshot_db_path(self.data_repo_root)
        connection = sqlite3.connect(db_path)
        try:
            connection.execute(
                "DELETE FROM php_native_snapshots WHERE snapshot_id = ?",
                ("compose-reply/thread-compose-fallback-001/reply-compose-fallback-001",),
            )
            connection.commit()
        finally:
            connection.close()

        compose_response = self.php_request(
            "/compose/reply",
            query_string="thread_id=thread-compose-fallback-001&parent_id=reply-compose-fallback-001",
        )

        self.assertEqual(compose_response["status"], 200)
        self.assertIn("X-Forum-Php-Native-Fallback: snapshot-missing", compose_response["headers"])
        self.assertNotIn("X-Forum-Php-Native: HIT", compose_response["headers"])
        self.assertIn("Reply body for fallback compose reply.", compose_response["body"])
        self.assertEqual(
            self.php_native_counter_value(
                "/compose/reply?thread_id=thread-compose-fallback-001&parent_id=reply-compose-fallback-001",
                "anonymous",
                "snapshot_missing",
            ),
            1,
        )

    def test_create_thread_write_path_warms_root_compose_reply_snapshot(self) -> None:
        payload = self.build_thread_payload(
            post_id="thread-compose-warm-001",
            subject="Compose reply warm path thread",
            body_text="Root body for compose reply warm path thread.",
        )
        response = self.php_request(
            "/api/create_thread",
            method="POST",
            body=self.build_create_thread_body(payload),
            content_type="application/json",
        )

        self.assertEqual(response["status"], 200)

        compose_response = self.php_request(
            "/compose/reply",
            query_string="thread_id=thread-compose-warm-001&parent_id=thread-compose-warm-001",
        )

        self.assertEqual(compose_response["status"], 200)
        self.assertIn("X-Forum-Php-Native: HIT", compose_response["headers"])
        self.assertIn("X-Forum-Response-Source: php-native-compose-reply", compose_response["headers"])
        self.assertIn("Compose reply warm path thread", compose_response["body"])

    def test_profile_route_can_render_from_php_native_snapshot_with_identity_hint_cookie(self) -> None:
        payload = self.build_thread_payload(
            post_id="thread-profile-native-001",
            subject="Profile native seed",
            body_text="Signed body for profile native seed.",
        )
        response = self.php_request(
            "/api/create_thread",
            method="POST",
            body=self.build_create_thread_body(payload),
            content_type="application/json",
        )
        self.assertEqual(response["status"], 200)

        rebuild_php_native_profile_snapshots(self.data_repo_root)

        profile_response = self.php_request(f"/profiles/{self.profile_slug()}", cookie="forum_identity_hint=test")

        self.assertEqual(profile_response["status"], 200)
        self.assertIn("X-Forum-Php-Native: HIT", profile_response["headers"])
        self.assertIn("X-Forum-Response-Source: php-native-profile", profile_response["headers"])

    def test_profile_route_with_unexpected_cookie_bypasses_php_native_snapshot(self) -> None:
        payload = self.build_thread_payload(
            post_id="thread-profile-fallback-001",
            subject="Profile fallback seed",
            body_text="Signed body for profile fallback seed.",
        )
        response = self.php_request(
            "/api/create_thread",
            method="POST",
            body=self.build_create_thread_body(payload),
            content_type="application/json",
        )
        self.assertEqual(response["status"], 200)

        rebuild_php_native_profile_snapshots(self.data_repo_root)

        profile_response = self.php_request(f"/profiles/{self.profile_slug()}", cookie="session=abc")

        self.assertEqual(profile_response["status"], 200)
        self.assertNotIn("X-Forum-Php-Native: HIT", profile_response["headers"])
        self.assertIn("Profile fallback seed", profile_response["body"])

    def test_thread_static_html_takes_precedence_over_native_snapshot(self) -> None:
        payload = self.build_thread_payload(
            post_id="thread-static-first-001",
            subject="Should be shadowed",
            body_text="Dynamic body.",
        )
        response = self.php_request(
            "/api/create_thread",
            method="POST",
            body=self.build_create_thread_body(payload),
            content_type="application/json",
        )
        self.assertEqual(response["status"], 200)
        rebuild_php_native_thread_snapshots(self.data_repo_root)
        self.write_static_thread_html("thread-static-first-001", "<html><body>Static wins</body></html>")

        thread_response = self.php_request("/threads/thread-static-first-001")

        self.assertEqual(thread_response["status"], 200)
        self.assertIn("X-Forum-Static-Html: HIT", thread_response["headers"])
        self.assertNotIn("X-Forum-Php-Native: HIT", thread_response["headers"])
        self.assertIn("Static wins", thread_response["body"])
        self.assertEqual(
            self.php_native_counter_value("/threads/thread-static-first-001", "anonymous", "native_hit"),
            0,
        )

    def test_thread_snapshot_miss_falls_through_and_is_counted(self) -> None:
        payload = self.build_thread_payload(
            post_id="thread-fallback-001",
            subject="Fallback thread",
            body_text="Fallback body.",
        )
        response = self.php_request(
            "/api/create_thread",
            method="POST",
            body=self.build_create_thread_body(payload),
            content_type="application/json",
        )
        self.assertEqual(response["status"], 200)
        db_path = thread_snapshot_db_path(self.data_repo_root)
        connection = sqlite3.connect(db_path)
        try:
            connection.execute("DELETE FROM php_native_snapshots WHERE snapshot_id = ?", ("thread/thread-fallback-001",))
            connection.commit()
        finally:
            connection.close()

        thread_response = self.php_request("/threads/thread-fallback-001")

        self.assertEqual(thread_response["status"], 200)
        self.assertIn("X-Forum-Php-Native-Fallback: snapshot-missing", thread_response["headers"])
        self.assertNotIn("X-Forum-Php-Native: HIT", thread_response["headers"])
        self.assertIn("Fallback thread", thread_response["body"])
        self.assertEqual(
            self.php_native_counter_value("/threads/thread-fallback-001", "anonymous", "snapshot_missing"),
            1,
        )

    def test_instance_page_uses_static_html_with_identity_hint_cookie(self) -> None:
        first = self.php_request("/instance/", cookie="forum_identity_hint=test")

        self.assertEqual(first["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", first["headers"])
        self.assertIn("Project FAQ", first["body"])
        self.assertEqual(
            self.static_html_files(),
            [Path(self.static_tempdir.name) / "_static_html" / "instance" / "index.html"],
        )

        second = self.php_request("/instance/", cookie="forum_identity_hint=test")

        self.assertEqual(second["status"], 200)
        self.assertIn("X-Forum-Static-Html: HIT", second["headers"])
        self.assertIn("Project FAQ", second["body"])

    def test_board_index_uses_cache_with_identity_hint_cookie_when_cta_is_disabled(self) -> None:
        previous_value = os.environ.get("FORUM_ENABLE_USERNAME_CLAIM_CTA")
        os.environ["FORUM_ENABLE_USERNAME_CLAIM_CTA"] = "0"
        try:
            first = self.php_request("/", cookie="forum_identity_hint=test")
            second = self.php_request("/", cookie="forum_identity_hint=test")
        finally:
            if previous_value is None:
                os.environ.pop("FORUM_ENABLE_USERNAME_CLAIM_CTA", None)
            else:
                os.environ["FORUM_ENABLE_USERNAME_CLAIM_CTA"] = previous_value

        self.assertEqual(first["status"], 200)
        self.assertEqual(second["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", first["headers"])
        self.assertIn("X-Forum-Static-Html: HIT", second["headers"])
        self.assertNotIn("data-username-claim-cta", first["body"])
        self.assertNotIn("data-username-claim-cta", second["body"])

    def test_compose_thread_uses_cache_with_identity_hint_cookie_when_cta_is_disabled(self) -> None:
        previous_value = os.environ.get("FORUM_ENABLE_USERNAME_CLAIM_CTA")
        os.environ["FORUM_ENABLE_USERNAME_CLAIM_CTA"] = "0"
        try:
            first = self.php_request("/compose/thread", cookie="forum_identity_hint=test")
            second = self.php_request("/compose/thread", cookie="forum_identity_hint=test")
        finally:
            if previous_value is None:
                os.environ.pop("FORUM_ENABLE_USERNAME_CLAIM_CTA", None)
            else:
                os.environ["FORUM_ENABLE_USERNAME_CLAIM_CTA"] = previous_value

        self.assertEqual(first["status"], 200)
        self.assertEqual(second["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", first["headers"])
        self.assertIn("X-Forum-Static-Html: HIT", second["headers"])
        self.assertNotIn("data-username-claim-cta", first["body"])
        self.assertNotIn("data-username-claim-cta", second["body"])
        self.assertIn("Compose a signed thread", first["body"])
        self.assertIn("Compose a signed thread", second["body"])

    def test_activity_page_uses_cache_with_identity_hint_cookie_when_cta_is_disabled(self) -> None:
        previous_value = os.environ.get("FORUM_ENABLE_USERNAME_CLAIM_CTA")
        os.environ["FORUM_ENABLE_USERNAME_CLAIM_CTA"] = "0"
        try:
            first = self.php_request("/activity/", cookie="forum_identity_hint=test")
            second = self.php_request("/activity/", cookie="forum_identity_hint=test")
        finally:
            if previous_value is None:
                os.environ.pop("FORUM_ENABLE_USERNAME_CLAIM_CTA", None)
            else:
                os.environ["FORUM_ENABLE_USERNAME_CLAIM_CTA"] = previous_value

        self.assertEqual(first["status"], 200)
        self.assertEqual(second["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", first["headers"])
        self.assertIn("X-Forum-Static-Html: HIT", second["headers"])
        self.assertNotIn("data-username-claim-cta", first["body"])
        self.assertNotIn("data-username-claim-cta", second["body"])
        self.assertIn("Repository activity", first["body"])
        self.assertIn("Repository activity", second["body"])


if __name__ == "__main__":
    unittest.main()
