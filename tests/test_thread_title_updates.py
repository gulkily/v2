from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from forum_core.identity import build_identity_id
from forum_core.thread_title_updates import (
    load_thread_title_update_records,
    normalize_thread_title,
    parse_thread_title_update_text,
    resolve_current_thread_title,
    signer_can_update_thread_title,
    thread_title_any_user_edit_enabled,
    thread_title_updates_dir,
)


class ThreadTitleUpdateTests(unittest.TestCase):
    def test_feature_flag_defaults_to_disabled(self) -> None:
        self.assertFalse(thread_title_any_user_edit_enabled({}))

    def test_feature_flag_accepts_truthy_values(self) -> None:
        self.assertTrue(thread_title_any_user_edit_enabled({"FORUM_ENABLE_THREAD_TITLE_ANY_USER_EDIT": "1"}))
        self.assertTrue(thread_title_any_user_edit_enabled({"FORUM_ENABLE_THREAD_TITLE_ANY_USER_EDIT": "true"}))
        self.assertTrue(thread_title_any_user_edit_enabled({"FORUM_ENABLE_THREAD_TITLE_ANY_USER_EDIT": "yes"}))

    def test_feature_flag_rejects_falsey_values(self) -> None:
        self.assertFalse(thread_title_any_user_edit_enabled({"FORUM_ENABLE_THREAD_TITLE_ANY_USER_EDIT": "0"}))
        self.assertFalse(thread_title_any_user_edit_enabled({"FORUM_ENABLE_THREAD_TITLE_ANY_USER_EDIT": "off"}))

    def test_parse_thread_title_update_text(self) -> None:
        record = parse_thread_title_update_text(
            dedent(
                """
                Record-ID: thread-title-update-001
                Thread-ID: thread-001
                Timestamp: 2026-03-28T12:00:00Z

                Better title
                """
            ).lstrip()
        )
        self.assertEqual(record.record_id, "thread-title-update-001")
        self.assertEqual(record.thread_id, "thread-001")
        self.assertEqual(record.timestamp, "2026-03-28T12:00:00Z")
        self.assertEqual(record.title, "Better title")

    def test_parse_requires_required_headers(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required headers"):
            parse_thread_title_update_text(
                "Record-ID: thread-title-update-001\n\nMissing thread and timestamp\n"
            )

    def test_normalize_rejects_non_ascii_or_multiline_or_blank(self) -> None:
        for value, message in [
            ("", "must not be blank"),
            ("hello\nworld", "single line"),
            ("caf\xe9", "ASCII"),
        ]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, message):
                    normalize_thread_title(value)

    def test_resolve_current_thread_title_prefers_latest_update(self) -> None:
        updates = [
            parse_thread_title_update_text(
                dedent(
                    """
                    Record-ID: thread-title-update-001
                    Thread-ID: thread-001
                    Timestamp: 2026-03-28T12:00:00Z

                    First rename
                    """
                ).lstrip()
            ),
            parse_thread_title_update_text(
                dedent(
                    """
                    Record-ID: thread-title-update-002
                    Thread-ID: thread-001
                    Timestamp: 2026-03-28T12:05:00Z

                    Second rename
                    """
                ).lstrip()
            ),
        ]
        self.assertEqual(
            resolve_current_thread_title(
                thread_id="thread-001",
                root_subject="Original title",
                updates=updates,
            ),
            "Second rename",
        )

    def test_load_thread_title_update_records_reads_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo_root = Path(tempdir)
            records_path = thread_title_updates_dir(repo_root)
            records_path.mkdir(parents=True, exist_ok=True)
            (records_path / "thread-title-update-001.txt").write_text(
                dedent(
                    """
                    Record-ID: thread-title-update-001
                    Thread-ID: thread-001
                    Timestamp: 2026-03-28T12:00:00Z

                    Better title
                    """
                ).lstrip(),
                encoding="ascii",
            )

            records = load_thread_title_update_records(records_path)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].thread_id, "thread-001")
        self.assertEqual(records[0].title, "Better title")

    def test_owner_can_update_thread_title(self) -> None:
        owner_identity_id = build_identity_id("ABCDEF0123456789ABCDEF0123456789ABCDEF01")
        self.assertTrue(
            signer_can_update_thread_title(
                thread_owner_identity_id=owner_identity_id,
                signer_identity_id=owner_identity_id,
                signer_fingerprint="ABCDEF0123456789ABCDEF0123456789ABCDEF01",
            )
        )

    def test_authorized_moderator_can_update_thread_title(self) -> None:
        self.assertTrue(
            signer_can_update_thread_title(
                thread_owner_identity_id=build_identity_id("ABCDEF0123456789ABCDEF0123456789ABCDEF01"),
                signer_identity_id=build_identity_id("1111111111111111111111111111111111111111"),
                signer_fingerprint="9999999999999999999999999999999999999999",
                env={"FORUM_MODERATOR_FINGERPRINTS": "9999999999999999999999999999999999999999"},
            )
        )

    def test_any_signed_user_can_update_when_flag_is_enabled(self) -> None:
        self.assertTrue(
            signer_can_update_thread_title(
                thread_owner_identity_id=build_identity_id("ABCDEF0123456789ABCDEF0123456789ABCDEF01"),
                signer_identity_id=build_identity_id("1111111111111111111111111111111111111111"),
                signer_fingerprint="1111111111111111111111111111111111111111",
                env={"FORUM_ENABLE_THREAD_TITLE_ANY_USER_EDIT": "1"},
            )
        )

    def test_non_owner_non_moderator_cannot_update_when_flag_is_disabled(self) -> None:
        self.assertFalse(
            signer_can_update_thread_title(
                thread_owner_identity_id=build_identity_id("ABCDEF0123456789ABCDEF0123456789ABCDEF01"),
                signer_identity_id=build_identity_id("1111111111111111111111111111111111111111"),
                signer_fingerprint="1111111111111111111111111111111111111111",
                env={},
            )
        )


if __name__ == "__main__":
    unittest.main()
