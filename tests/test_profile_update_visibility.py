from __future__ import annotations

import unittest

from forum_core.identity import ProfileSummary
from forum_web.profiles import (
    IdentityContext,
    profile_can_update_username,
    profile_username_claim_callout_text,
)


class FakeResolution:
    def canonical_identity_id(self, identity_id: str | None) -> str | None:
        if identity_id == "openpgp:alpha":
            return "openpgp:alpha"
        return None

    def member_identity_ids(self, identity_id: str | None) -> tuple[str, ...]:
        if identity_id == "openpgp:alpha":
            return ("openpgp:alpha",)
        return ()


def make_summary() -> ProfileSummary:
    return ProfileSummary(
        identity_id="openpgp:alpha",
        bootstrap_identity_id="openpgp:alpha",
        signer_fingerprint="AAAAAAAAAAAAAAAA",
        display_name="Alpha",
        display_name_source="fingerprint_fallback",
        fallback_display_name="AAAAAAAAAAAAAAAA",
        bootstrap_record_id="identity-openpgp-alpha",
        bootstrap_post_id="alpha-root",
        bootstrap_thread_id="alpha-root",
        bootstrap_path="records/identity/identity-openpgp-alpha.txt",
        member_identity_ids=("openpgp:alpha",),
        post_ids=("alpha-root",),
        thread_ids=("alpha-root",),
        public_key_text="alpha",
    )


class ProfileUpdateVisibilityTests(unittest.TestCase):
    def test_profile_is_eligible_without_visible_claim(self) -> None:
        summary = make_summary()
        identity_context = IdentityContext(
            bootstraps_by_identity_id={},
            resolution=FakeResolution(),
            profile_update_records=(),
            merge_request_records=(),
            merge_request_states=(),
        )

        self.assertTrue(profile_can_update_username(summary=summary, identity_context=identity_context))

    def test_profile_is_ineligible_after_visible_claim(self) -> None:
        summary = make_summary()
        claim = type("Claim", (), {"source_identity_id": "openpgp:alpha", "record_id": "profile-update-alpha"})()
        identity_context = IdentityContext(
            bootstraps_by_identity_id={},
            resolution=FakeResolution(),
            profile_update_records=(claim,),
            merge_request_records=(),
            merge_request_states=(),
        )

        self.assertFalse(profile_can_update_username(summary=summary, identity_context=identity_context))

    def test_callout_text_is_present_for_eligible_profile(self) -> None:
        summary = make_summary()
        identity_context = IdentityContext(
            bootstraps_by_identity_id={},
            resolution=FakeResolution(),
            profile_update_records=(),
            merge_request_records=(),
            merge_request_states=(),
        )

        self.assertEqual(
            profile_username_claim_callout_text(summary=summary, identity_context=identity_context),
            "You can still claim one username for this profile.",
        )

    def test_callout_text_is_empty_for_ineligible_profile(self) -> None:
        summary = make_summary()
        claim = type("Claim", (), {"source_identity_id": "openpgp:alpha", "record_id": "profile-update-alpha"})()
        identity_context = IdentityContext(
            bootstraps_by_identity_id={},
            resolution=FakeResolution(),
            profile_update_records=(claim,),
            merge_request_records=(),
            merge_request_states=(),
        )

        self.assertEqual(
            profile_username_claim_callout_text(summary=summary, identity_context=identity_context),
            "",
        )


if __name__ == "__main__":
    unittest.main()
