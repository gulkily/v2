from __future__ import annotations

import unittest
from pathlib import Path

from forum_core.profile_updates import normalize_display_name, parse_profile_update_text


class ProfileUpdateUsernameValidationTests(unittest.TestCase):
    def test_accepts_lowercase_alphanumeric_and_single_hyphen_usernames(self) -> None:
        self.assertEqual(normalize_display_name("quiet-river", strict_username=True), "quiet-river")
        self.assertEqual(normalize_display_name("user42", strict_username=True), "user42")

    def test_rejects_uppercase_and_punctuation(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "display name must use lowercase ASCII letters, digits, and single hyphens only",
        ):
            normalize_display_name("QuietRiver", strict_username=True)
        with self.assertRaisesRegex(
            ValueError,
            "display name must use lowercase ASCII letters, digits, and single hyphens only",
        ):
            normalize_display_name("quiet_river", strict_username=True)

    def test_rejects_consecutive_hyphens_and_short_values(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "display name must use lowercase ASCII letters, digits, and single hyphens only",
        ):
            normalize_display_name("quiet--river", strict_username=True)
        with self.assertRaisesRegex(ValueError, "display name must be at least 3 characters"):
            normalize_display_name("aa", strict_username=True)

    def test_rejects_reserved_names(self) -> None:
        with self.assertRaisesRegex(ValueError, "display name is reserved"):
            normalize_display_name("admin", strict_username=True)

    def test_legacy_stored_profile_update_names_remain_loadable(self) -> None:
        record = parse_profile_update_text(
            "\n".join(
                [
                    "Record-ID: profile-update-legacy",
                    "Action: set_display_name",
                    "Source-Identity-ID: openpgp:0123456789abcdef",
                    "Timestamp: 2026-03-14T12:00:00Z",
                    "",
                    "BrightName",
                    "",
                ]
            ),
            source_path=Path("records/profile-updates/profile-update-legacy.txt"),
        )
        self.assertEqual(record.display_name, "BrightName")


if __name__ == "__main__":
    unittest.main()
