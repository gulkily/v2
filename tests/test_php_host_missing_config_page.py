from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class PhpHostMissingConfigPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.tempdir = tempfile.TemporaryDirectory()
        self.public_dir = Path(self.tempdir.name) / "public"
        self.public_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.public_dir / "index.php"
        self.cache_path = self.public_dir / "cache.php"
        self.index_path.write_text(
            (self.repo_root / "php_host" / "public" / "index.php").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.cache_path.write_text(
            (self.repo_root / "php_host" / "public" / "cache.php").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def php_request(self) -> tuple[int, list[str], str]:
        env = os.environ.copy()
        env.update(
            {
                "GATEWAY_INTERFACE": "CGI/1.1",
                "REDIRECT_STATUS": "200",
                "REQUEST_METHOD": "GET",
                "REQUEST_URI": "/",
                "QUERY_STRING": "",
                "SERVER_NAME": "localhost",
                "SERVER_PORT": "80",
                "SERVER_PROTOCOL": "HTTP/1.1",
                "SCRIPT_FILENAME": str(self.index_path),
                "SCRIPT_NAME": "/index.php",
                "CONTENT_TYPE": "",
                "CONTENT_LENGTH": "0",
            }
        )
        result = subprocess.run(
            ["php-cgi", "-q", str(self.index_path)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        raw_headers, body = result.stdout.split("\n\n", 1)
        header_lines = [line.rstrip("\r") for line in raw_headers.splitlines() if line]
        status_line = next((line for line in header_lines if line.startswith("Status: ")), "Status: 200 OK")
        status_code = int(status_line.split(" ", 2)[1])
        return status_code, [line for line in header_lines if not line.startswith("Status: ")], body

    def test_missing_config_page_is_styled_and_actionable(self) -> None:
        status, headers, body = self.php_request()

        self.assertEqual(status, 500)
        self.assertIn("Content-Type: text/html; charset=utf-8", headers)
        self.assertIn("<title>PHP host setup required</title>", body)
        self.assertIn("forum_host_config.php", body)
        self.assertIn(str(self.public_dir / "forum_host_config.php"), body)
        self.assertIn("./forum php-host-setup /absolute/path/to/public-web-root", body)
        self.assertIn("docs/php_primary_host_installation.md", body)
        self.assertIn("<main>\n    <section class=\"hero\">", body)


if __name__ == "__main__":
    unittest.main()
