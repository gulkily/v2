from __future__ import annotations

import unittest
from pathlib import Path


class PhpHostHtaccessTests(unittest.TestCase):
    def test_htaccess_includes_static_html_bypass_guards_and_routes(self) -> None:
        contents = (
            Path(__file__).resolve().parent.parent / "php_host" / "public" / ".htaccess"
        ).read_text(encoding="utf-8")

        self.assertIn("RewriteCond %{REQUEST_METHOD} =GET", contents)
        self.assertIn("RewriteCond %{QUERY_STRING} ^$", contents)
        self.assertIn("RewriteCond %{HTTP:Authorization} ^$", contents)
        self.assertIn("RewriteCond %{HTTP:Cookie} ^$", contents)
        self.assertIn("RewriteCond %{DOCUMENT_ROOT}/_static_html/index.html -f", contents)
        self.assertIn("RewriteRule ^$ _static_html/index.html [L]", contents)
        self.assertIn("RewriteRule ^threads/([^/]+)/?$ _static_html/threads/$1/index.html [L]", contents)
        self.assertIn("RewriteRule ^posts/([^/]+)/?$ _static_html/posts/$1/index.html [L]", contents)
        self.assertIn(
            "RewriteRule ^planning/tasks/([^/]+)/?$ _static_html/planning/tasks/$1/index.html [L]",
            contents,
        )
        self.assertIn("RewriteRule ^profiles/([^/]+)/?$ _static_html/profiles/$1/index.html [L]", contents)
        self.assertTrue(contents.strip().endswith("RewriteRule ^ index.php [L,QSA]"))


if __name__ == "__main__":
    unittest.main()
