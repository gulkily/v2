from __future__ import annotations

import unittest

from forum_core.profile_updates import prevent_duplicate_usernames_enabled


class ProfileUpdateFeatureFlagTests(unittest.TestCase):
    def test_duplicate_username_flag_defaults_to_disabled(self) -> None:
        self.assertFalse(prevent_duplicate_usernames_enabled({}))

    def test_duplicate_username_flag_accepts_truthy_values(self) -> None:
        self.assertTrue(prevent_duplicate_usernames_enabled({"FORUM_PREVENT_DUPLICATE_USERNAMES": "1"}))
        self.assertTrue(prevent_duplicate_usernames_enabled({"FORUM_PREVENT_DUPLICATE_USERNAMES": "true"}))
        self.assertTrue(prevent_duplicate_usernames_enabled({"FORUM_PREVENT_DUPLICATE_USERNAMES": "yes"}))

    def test_duplicate_username_flag_rejects_falsey_values(self) -> None:
        self.assertFalse(prevent_duplicate_usernames_enabled({"FORUM_PREVENT_DUPLICATE_USERNAMES": "0"}))
        self.assertFalse(prevent_duplicate_usernames_enabled({"FORUM_PREVENT_DUPLICATE_USERNAMES": "off"}))


if __name__ == "__main__":
    unittest.main()
