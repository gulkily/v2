from __future__ import annotations

import unittest

from forum_web.templates import merge_feature_enabled


class MergeFeatureFlagTests(unittest.TestCase):
    def test_merge_feature_flag_defaults_to_disabled(self) -> None:
        self.assertFalse(merge_feature_enabled({}))

    def test_merge_feature_flag_accepts_truthy_values(self) -> None:
        self.assertTrue(merge_feature_enabled({"FORUM_ENABLE_ACCOUNT_MERGE": "1"}))
        self.assertTrue(merge_feature_enabled({"FORUM_ENABLE_ACCOUNT_MERGE": "true"}))
        self.assertTrue(merge_feature_enabled({"FORUM_ENABLE_ACCOUNT_MERGE": "yes"}))

    def test_merge_feature_flag_rejects_falsey_values(self) -> None:
        self.assertFalse(merge_feature_enabled({"FORUM_ENABLE_ACCOUNT_MERGE": "0"}))
        self.assertFalse(merge_feature_enabled({"FORUM_ENABLE_ACCOUNT_MERGE": "off"}))


if __name__ == "__main__":
    unittest.main()
