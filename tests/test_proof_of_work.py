from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from forum_core.identity import build_bootstrap_payload, build_identity_id
from forum_core.proof_of_work import (
    DEFAULT_POW_DIFFICULTY,
    first_post_pow_difficulty,
    first_post_pow_enabled,
    pow_required_for_signed_post,
)


class ProofOfWorkTests(unittest.TestCase):
    def test_first_post_pow_enabled_accepts_common_truthy_values(self) -> None:
        self.assertTrue(first_post_pow_enabled({"FORUM_ENABLE_FIRST_POST_POW": "1"}))
        self.assertTrue(first_post_pow_enabled({"FORUM_ENABLE_FIRST_POST_POW": "true"}))
        self.assertFalse(first_post_pow_enabled({"FORUM_ENABLE_FIRST_POST_POW": "0"}))
        self.assertFalse(first_post_pow_enabled({}))

    def test_first_post_pow_difficulty_defaults_and_validates(self) -> None:
        self.assertEqual(first_post_pow_difficulty({}), DEFAULT_POW_DIFFICULTY)
        self.assertEqual(first_post_pow_difficulty({"FORUM_FIRST_POST_POW_DIFFICULTY": "20"}), 20)

        with self.assertRaisesRegex(ValueError, "decimal integer"):
            first_post_pow_difficulty({"FORUM_FIRST_POST_POW_DIFFICULTY": "hard"})

        with self.assertRaisesRegex(ValueError, "at least 1"):
            first_post_pow_difficulty({"FORUM_FIRST_POST_POW_DIFFICULTY": "0"})

    def test_pow_required_for_signed_post_checks_existing_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo_root = Path(tempdir)
            fingerprint = "ABCDEF0123456789ABCDEF0123456789ABCDEF01"

            self.assertTrue(pow_required_for_signed_post(repo_root=repo_root, signer_fingerprint=fingerprint))

            identity_id = build_identity_id(fingerprint)
            record_id, payload = build_bootstrap_payload(
                identity_id=identity_id,
                signer_fingerprint=fingerprint,
                bootstrap_post_id="thread-001",
                bootstrap_thread_id="thread-001",
                public_key_text="-----BEGIN PGP PUBLIC KEY BLOCK-----\nabc\n-----END PGP PUBLIC KEY BLOCK-----",
            )
            identity_path = repo_root / "records" / "identity" / f"{record_id}.txt"
            identity_path.parent.mkdir(parents=True, exist_ok=True)
            identity_path.write_text(payload, encoding="ascii")

            self.assertFalse(pow_required_for_signed_post(repo_root=repo_root, signer_fingerprint=fingerprint))


if __name__ == "__main__":
    unittest.main()
