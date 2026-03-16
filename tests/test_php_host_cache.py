from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent


class PhpHostCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.index_path = self.repo_root / "php_host" / "public" / "index.php"
        self.openpgp_module_url = (
            self.repo_root / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        self.repo_tempdir = tempfile.TemporaryDirectory()
        self.cache_tempdir = tempfile.TemporaryDirectory()
        self.data_repo_root = Path(self.repo_tempdir.name)
        (self.data_repo_root / "records" / "posts").mkdir(parents=True, exist_ok=True)

        self.run_command(["git", "init"], cwd=self.data_repo_root)
        self.run_command(["git", "config", "user.name", "Codex Test"], cwd=self.data_repo_root)
        self.run_command(["git", "config", "user.email", "codex@example.com"], cwd=self.data_repo_root)

        self.user_keys = self.generate_signing_keypair("PHP Host Cache Test")

    def tearDown(self) -> None:
        self.cache_tempdir.cleanup()
        self.repo_tempdir.cleanup()

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
    ) -> dict[str, object]:
        env = os.environ.copy()
        env.update(
            {
                "FORUM_PHP_APP_ROOT": str(self.repo_root),
                "FORUM_REPO_ROOT": str(self.data_repo_root),
                "FORUM_PHP_CACHE_DIR": str(Path(self.cache_tempdir.name) / "cache"),
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

    def cache_files(self) -> list[Path]:
        cache_root = Path(self.cache_tempdir.name) / "cache"
        if not cache_root.exists():
            return []
        return sorted(path for path in cache_root.glob("*.cgi"))

    def test_php_host_caches_allowlisted_reads_and_marks_hit_headers(self) -> None:
        first = self.php_request("/")
        second = self.php_request("/")

        self.assertEqual(first["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", first["headers"])
        self.assertEqual(second["status"], 200)
        self.assertIn("X-Forum-Php-Cache: HIT", second["headers"])
        self.assertEqual(first["body"], second["body"])
        self.assertEqual(len(self.cache_files()), 1)

    def test_php_host_sets_asset_cache_headers_without_microcaching_assets(self) -> None:
        response = self.php_request("/assets/site.css")

        self.assertEqual(response["status"], 200)
        self.assertIn("X-Forum-Php-Cache: MISS", response["headers"])
        self.assertIn("Cache-Control: public, max-age=3600", response["headers"])
        self.assertEqual(self.cache_files(), [])

    def test_successful_write_clears_php_microcache(self) -> None:
        warm = self.php_request("/")
        self.assertIn("X-Forum-Php-Cache: MISS", warm["headers"])
        self.assertEqual(len(self.cache_files()), 1)

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

        refreshed = self.php_request("/")
        self.assertIn("X-Forum-Php-Cache: MISS", refreshed["headers"])
        self.assertIn("thread-php-cache-001", refreshed["body"])


if __name__ == "__main__":
    unittest.main()
