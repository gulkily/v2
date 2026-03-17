from __future__ import annotations

import unittest
from pathlib import Path

from forum_core.identity_links import derive_identity_resolution
from forum_core.merge_requests import (
    derive_approved_merge_links,
    derive_historical_username_matches,
    derive_merge_request_states,
    parse_merge_request_text,
)
from forum_core.profile_updates import parse_profile_update_text


class MergeRequestTests(unittest.TestCase):
    def test_parse_merge_request_text_requires_headers(self) -> None:
        record = parse_merge_request_text(
            (
                "Record-ID: merge-request-001\n"
                "Action: request_merge\n"
                "Requester-Identity-ID: openpgp:alpha\n"
                "Target-Identity-ID: openpgp:beta\n"
                "Actor-Identity-ID: openpgp:alpha\n"
                "Timestamp: 2026-03-17T23:00:00Z\n"
                "\n"
                "please merge\n"
            ),
            source_path=Path("request.txt"),
        )

        self.assertEqual(record.record_id, "merge-request-001")
        self.assertEqual(record.action, "request_merge")
        self.assertEqual(record.requester_identity_id, "openpgp:alpha")
        self.assertEqual(record.target_identity_id, "openpgp:beta")
        self.assertEqual(record.actor_identity_id, "openpgp:alpha")
        self.assertEqual(record.note, "please merge")

    def test_target_approval_activates_merge(self) -> None:
        states = derive_merge_request_states(
            [
                parse_merge_request_text(
                    (
                        "Record-ID: merge-request-001\n"
                        "Action: request_merge\n"
                        "Requester-Identity-ID: openpgp:alpha\n"
                        "Target-Identity-ID: openpgp:beta\n"
                        "Actor-Identity-ID: openpgp:alpha\n"
                        "Timestamp: 2026-03-17T23:00:00Z\n\n"
                    )
                ),
                parse_merge_request_text(
                    (
                        "Record-ID: merge-request-002\n"
                        "Action: approve_merge\n"
                        "Requester-Identity-ID: openpgp:alpha\n"
                        "Target-Identity-ID: openpgp:beta\n"
                        "Actor-Identity-ID: openpgp:beta\n"
                        "Timestamp: 2026-03-17T23:05:00Z\n\n"
                    )
                ),
            ]
        )

        self.assertEqual(len(states), 1)
        self.assertTrue(states[0].approved_by_target)
        self.assertTrue(states[0].active_merge)
        self.assertFalse(states[0].pending)

        links = derive_approved_merge_links(states)
        self.assertEqual(len(links), 2)

    def test_moderator_approval_activates_merge(self) -> None:
        states = derive_merge_request_states(
            [
                parse_merge_request_text(
                    (
                        "Record-ID: merge-request-010\n"
                        "Action: request_merge\n"
                        "Requester-Identity-ID: openpgp:alpha\n"
                        "Target-Identity-ID: openpgp:beta\n"
                        "Actor-Identity-ID: openpgp:alpha\n"
                        "Timestamp: 2026-03-17T23:00:00Z\n\n"
                    )
                ),
                parse_merge_request_text(
                    (
                        "Record-ID: merge-request-011\n"
                        "Action: moderator_approve_merge\n"
                        "Requester-Identity-ID: openpgp:alpha\n"
                        "Target-Identity-ID: openpgp:beta\n"
                        "Actor-Identity-ID: openpgp:moderator\n"
                        "Timestamp: 2026-03-17T23:04:00Z\n\n"
                    )
                ),
            ]
        )

        self.assertTrue(states[0].approved_by_moderator)
        self.assertTrue(states[0].active_merge)
        self.assertFalse(states[0].pending)

    def test_dismiss_clears_pending_until_new_request(self) -> None:
        states = derive_merge_request_states(
            [
                parse_merge_request_text(
                    (
                        "Record-ID: merge-request-020\n"
                        "Action: request_merge\n"
                        "Requester-Identity-ID: openpgp:alpha\n"
                        "Target-Identity-ID: openpgp:beta\n"
                        "Actor-Identity-ID: openpgp:alpha\n"
                        "Timestamp: 2026-03-17T23:00:00Z\n\n"
                    )
                ),
                parse_merge_request_text(
                    (
                        "Record-ID: merge-request-021\n"
                        "Action: dismiss_merge\n"
                        "Requester-Identity-ID: openpgp:alpha\n"
                        "Target-Identity-ID: openpgp:beta\n"
                        "Actor-Identity-ID: openpgp:beta\n"
                        "Timestamp: 2026-03-17T23:03:00Z\n\n"
                    )
                ),
            ]
        )

        self.assertTrue(states[0].dismissed)
        self.assertFalse(states[0].pending)
        self.assertFalse(states[0].active_merge)

    def test_historical_username_matches_use_visible_profile_history(self) -> None:
        resolution = derive_identity_resolution(
            visible_identity_ids=frozenset({"openpgp:alpha", "openpgp:beta", "openpgp:gamma"}),
            link_records=[],
        )
        updates = [
            parse_profile_update_text(
                (
                    "Record-ID: profile-update-001\n"
                    "Action: set_display_name\n"
                    "Source-Identity-ID: openpgp:alpha\n"
                    "Timestamp: 2026-03-17T22:00:00Z\n\n"
                    "Ilya\n"
                )
            ),
            parse_profile_update_text(
                (
                    "Record-ID: profile-update-002\n"
                    "Action: set_display_name\n"
                    "Source-Identity-ID: openpgp:alpha\n"
                    "Timestamp: 2026-03-17T22:10:00Z\n\n"
                    "Ilya G\n"
                )
            ),
            parse_profile_update_text(
                (
                    "Record-ID: profile-update-003\n"
                    "Action: set_display_name\n"
                    "Source-Identity-ID: openpgp:beta\n"
                    "Timestamp: 2026-03-17T22:20:00Z\n\n"
                    "Ilya\n"
                )
            ),
            parse_profile_update_text(
                (
                    "Record-ID: profile-update-004\n"
                    "Action: set_display_name\n"
                    "Source-Identity-ID: openpgp:gamma\n"
                    "Timestamp: 2026-03-17T22:30:00Z\n\n"
                    "Different\n"
                )
            ),
        ]

        matches = derive_historical_username_matches(
            identity_id="openpgp:alpha",
            resolution=resolution,
            profile_updates=updates,
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].candidate_identity_id, "openpgp:beta")
        self.assertEqual(matches[0].candidate_display_name, "Ilya")
        self.assertEqual(matches[0].shared_display_names, ("Ilya",))


if __name__ == "__main__":
    unittest.main()
