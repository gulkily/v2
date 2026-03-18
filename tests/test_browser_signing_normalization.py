from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class BrowserSigningNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.tempdir = tempfile.TemporaryDirectory()
        self.assets_root = Path(self.tempdir.name)
        (self.assets_root / "vendor").mkdir(parents=True, exist_ok=True)
        browser_signing_text = (
            self.repo_root / "templates" / "assets" / "browser_signing.js"
        ).read_text(encoding="utf-8").replace("./openpgp_loader.js", "./openpgp_loader.mjs")
        (self.assets_root / "browser_signing.mjs").write_text(
            browser_signing_text,
            encoding="utf-8",
        )
        shutil.copyfile(
            self.repo_root / "templates" / "assets" / "openpgp_loader.js",
            self.assets_root / "openpgp_loader.mjs",
        )
        shutil.copyfile(
            self.repo_root / "templates" / "assets" / "vendor" / "openpgp.min.mjs",
            self.assets_root / "vendor" / "openpgp.min.mjs",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_helper(self, text: str, *, remove_unsupported: bool = False) -> dict[str, object]:
        script = f"""
const mod = await import({json.dumps((self.assets_root / "browser_signing.mjs").as_uri())});
const result = mod.normalizeComposeAscii(
  {json.dumps(text)},
  {{ removeUnsupported: {str(remove_unsupported).lower()} }},
);
process.stdout.write(JSON.stringify(result));
"""
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)

    def run_expression(self, expression: str) -> dict[str, object]:
        script = f"""
const mod = await import({json.dumps((self.assets_root / "browser_signing.mjs").as_uri())});
const result = {expression};
process.stdout.write(JSON.stringify(result));
"""
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)

    def test_normalize_compose_ascii_rewrites_common_punctuation(self) -> None:
        result = self.run_helper('“hello”… — test')

        self.assertEqual(result["text"], '"hello"... - test')
        self.assertTrue(result["hadCorrections"])
        self.assertEqual(result["unsupportedCount"], 0)
        self.assertEqual(result["removedUnsupportedCount"], 0)

    def test_normalize_compose_ascii_reports_unsupported_characters(self) -> None:
        result = self.run_helper("emoji 🙂 test")

        self.assertEqual(result["text"], "emoji 🙂 test")
        self.assertFalse(result["hadCorrections"])
        self.assertEqual(result["unsupportedCount"], 1)
        self.assertEqual(result["removedUnsupportedCount"], 0)

    def test_normalize_compose_ascii_can_remove_unsupported_characters(self) -> None:
        result = self.run_helper("emoji 🙂 test", remove_unsupported=True)

        self.assertEqual(result["text"], "emoji  test")
        self.assertFalse(result["hadCorrections"])
        self.assertEqual(result["unsupportedCount"], 0)
        self.assertEqual(result["removedUnsupportedCount"], 1)

    def test_format_signing_status_mentions_unsigned_fallback_when_enabled(self) -> None:
        result = self.run_expression(
            """{
  message: mod.formatSigningStatus(
    "create_thread",
    { code: "missing_bigint", message: "no bigint" },
    { allowUnsignedFallback: true },
  ),
}"""
        )

        self.assertIn("Posting can still continue unsigned.", result["message"])

    def test_format_signing_status_mentions_required_signing_when_fallback_disabled(self) -> None:
        result = self.run_expression(
            """{
  message: mod.formatSigningStatus(
    "create_thread",
    { code: "missing_bigint", message: "no bigint" },
    { allowUnsignedFallback: false },
  ),
  label: mod.requiresSigningSubmitLabel("create_thread", { dryRun: false }),
}"""
        )

        self.assertIn("Unsigned fallback is disabled here, so signing is still required.", result["message"])
        self.assertEqual(result["label"], "Signing required to submit")

    def test_pending_submission_storage_key_separates_preview_from_publish(self) -> None:
        result = self.run_expression(
            """{
  publishKey: mod.pendingSubmissionStorageKey(
    "create_thread",
    { threadType: "", boardTags: "general", threadId: "", parentId: "" },
    { dryRun: false },
  ),
  previewKey: mod.pendingSubmissionStorageKey(
    "create_thread",
    { threadType: "", boardTags: "general", threadId: "", parentId: "" },
    { dryRun: true },
  ),
}"""
        )

        self.assertNotEqual(result["publishKey"], result["previewKey"])
        self.assertIn("publish", result["publishKey"])
        self.assertIn("dry-run", result["previewKey"])


if __name__ == "__main__":
    unittest.main()
