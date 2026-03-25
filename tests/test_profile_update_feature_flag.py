from __future__ import annotations

import unittest

from forum_core.profile_updates import prevent_duplicate_usernames_enabled
from forum_web.web import signing_debug_logging_enabled


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

    def test_signing_debug_flag_defaults_to_disabled(self) -> None:
        self.assertFalse(signing_debug_logging_enabled({}))

    def test_signing_debug_flag_accepts_truthy_values(self) -> None:
        self.assertTrue(signing_debug_logging_enabled({"FORUM_ENABLE_SIGNING_DEBUG_LOGS": "1"}))
        self.assertTrue(signing_debug_logging_enabled({"FORUM_ENABLE_SIGNING_DEBUG_LOGS": "true"}))
        self.assertTrue(signing_debug_logging_enabled({"FORUM_ENABLE_SIGNING_DEBUG_LOGS": "yes"}))

    def test_signing_debug_flag_rejects_falsey_values(self) -> None:
        self.assertFalse(signing_debug_logging_enabled({"FORUM_ENABLE_SIGNING_DEBUG_LOGS": "0"}))
        self.assertFalse(signing_debug_logging_enabled({"FORUM_ENABLE_SIGNING_DEBUG_LOGS": "off"}))


if __name__ == "__main__":
    unittest.main()
