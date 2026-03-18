1. Goal: enforce the one-username-claim-per-signer rule in the canonical profile-update write path.
Dependencies: approved Step 2; existing `/api/update_profile` validation and loaded profile-update record set.
Expected changes: extend profile-update validation with a helper such as `has_visible_username_claim(source_identity_id, profile_updates) -> bool`; reject later `set_display_name` submissions from a signer identity that already has one visible accepted claim, while leaving first claims and non-username read logic unchanged.
Verification approach: submit a first signed username claim for one identity, then submit a second claim from the same key and confirm deterministic rejection.
Risks or open questions:
- the rule must clearly define “already claimed” against current visible repository state only
- rejection text should be specific enough for browser users to understand why the second claim failed
Canonical components/API contracts touched: `/api/update_profile`; `forum_cgi/profile_updates.py`; existing profile-update record family.

2. Goal: reflect the one-claim policy clearly on the existing browser username-update surface.
Dependencies: Stage 1; current `/profiles/<identity-slug>/update` page and browser-signing feedback flow.
Expected changes: update the profile-update page copy and/or result handling so the user understands the claim is a one-time action per key pair; keep the page and payload structure shared with the current profile-update flow rather than introducing a new write surface.
Verification approach: manually load the update page before and after a first claim exists and confirm the page/result messaging remains understandable; confirm browser failure feedback shows the new deterministic rejection reason.
Risks or open questions:
- page messaging should discourage repeat attempts without implying broader account-management behavior
- avoid overexplaining linked-identity policy on a narrow write surface
Canonical components/API contracts touched: `/profiles/<identity-slug>/update`; `templates/profile_update.html`; existing browser signing/result UI.

3. Goal: preserve deterministic merged-profile reads while proving the new claim-limit policy does not break the current winner rule.
Dependencies: Stages 1-2; existing resolved display-name selection across linked identities.
Expected changes: add focused regression coverage showing that linked identities may each keep one accepted claim, that merged-profile reads still pick one deterministic visible winner, and that the same-key second claim fails without changing readback behavior.
Verification approach: run targeted tests for profile-update submission, merged profile pages, and username-route/profile read surfaces with fixtures where two linked identities each have one claim.
Risks or open questions:
- tests must cover both the blocked repeat-claim path and the unchanged merged-profile winner behavior
- winner behavior should remain explicit rather than being indirectly inferred from whichever test record happens to be newest
Canonical components/API contracts touched: profile-update submission tests; profile page tests; `/user/<username>` and `/profiles/<identity-slug>` read surfaces.
