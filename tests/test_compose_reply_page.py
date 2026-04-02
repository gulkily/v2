from __future__ import annotations

import unittest

from tests.helpers import ForumRepoTestCase


class ComposeReplyPageTests(ForumRepoTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: Root thread

            Root post body.
            """,
        )
        self.write_record(
            "records/posts/reply-001.txt",
            """
            Post-ID: reply-001
            Board-Tags: general
            Subject: Reply target
            Thread-ID: root-001
            Parent-ID: root-001

            Target reply body.
            Second line for context.
            """,
        )

    def get(self, path: str, query_string: str, *, extra_env: dict[str, str] | None = None) -> tuple[str, dict[str, str], str]:
        status, headers, body = self.request(path, query_string=query_string, extra_env=extra_env)
        return status, headers, str(body)

    def test_compose_reply_page_shows_parent_post_body(self) -> None:
        status, _, body = self.get(
            "/compose/reply",
            "thread_id=root-001&parent_id=reply-001",
        )

        self.assertEqual(status, "200 OK")
        self.assertIn("Replying to", body)
        self.assertIn("Target reply body.", body)
        self.assertIn("Second line for context.", body)
        self.assertIn("/posts/reply-001", body)
        self.assertNotIn("Signed Posting", body)
        self.assertNotIn('class="breadcrumb"', body)
        self.assertNotIn('<p class="post-id">', body)
        self.assertNotIn('<p class="post-tags">', body)
        self.assertNotIn('<p class="post-relation">', body)
        self.assertNotIn("<h2>Compose a signed reply</h2>", body)
        self.assertNotIn(">Signed Post<", body)
        self.assertIn('id="signed-post-form"', body)
        self.assertIn('id="draft-status"', body)
        self.assertIn('id="remove-unsupported-button"', body)
        self.assertIn('id="compose-normalization-status"', body)
        self.assertIn('class="compose-submit-area"', body)
        self.assertIn('id="submit-status"', body)
        self.assertIn('class="status-note compose-submit-status"', body)
        self.assertIn('data-status-tone="idle"', body)
        self.assertIn('data-unsigned-fallback-enabled="', body)
        self.assertIn("Requirements and limitations", body)
        self.assertIn("ASCII-only canonical text records", body)
        self.assertIn("reduces Unicode obfuscation risks", body)
        self.assertIn(">Technical details<", body)
        self.assertNotIn(">Advanced<", body)

        reference_index = body.index("Replying to")
        textarea_index = body.index('id="body-input"')
        submit_status_index = body.index('id="submit-status"')
        draft_status_index = body.index('id="draft-status"')
        requirements_index = body.index("Requirements and limitations")

        self.assertLess(reference_index, textarea_index)
        self.assertLess(textarea_index, draft_status_index)
        self.assertLess(textarea_index, submit_status_index)
        self.assertLess(submit_status_index, draft_status_index)
        self.assertLess(draft_status_index, requirements_index)

    def test_compose_reply_page_exposes_pow_settings_when_enabled(self) -> None:
        status, _, body = self.get(
            "/compose/reply",
            "thread_id=root-001&parent_id=reply-001",
            extra_env={
                "FORUM_ENABLE_FIRST_POST_POW": "1",
                "FORUM_FIRST_POST_POW_DIFFICULTY": "10",
            },
        )

        self.assertEqual(status, "200 OK")
        self.assertIn('data-pow-enabled="true"', body)
        self.assertIn('data-pow-difficulty="10"', body)

    def test_compose_reply_page_exposes_unsigned_fallback_flag_when_enabled(self) -> None:
        status, _, body = self.get(
            "/compose/reply",
            "thread_id=root-001&parent_id=reply-001",
            extra_env={"FORUM_ENABLE_UNSIGNED_POST_FALLBACK": "1"},
        )

        self.assertEqual(status, "200 OK")
        self.assertIn('data-unsigned-fallback-enabled="true"', body)

    def test_compose_reply_page_does_not_leak_hidden_parent_post(self) -> None:
        self.write_record(
            "records/moderation/hide-reply-001.txt",
            """
            Record-ID: hide-reply-001
            Action: hide
            Target-Type: post
            Target-ID: reply-001
            Timestamp: 2026-03-14T12:00:00Z

            Hidden for moderation.
            """,
        )

        status, _, body = self.get(
            "/compose/reply",
            "thread_id=root-001&parent_id=reply-001",
        )

        self.assertEqual(status, "404 Not Found")
        self.assertNotIn("Target reply body.", body)


if __name__ == "__main__":
    unittest.main()
