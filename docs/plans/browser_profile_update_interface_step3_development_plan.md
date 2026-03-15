## Stage 1
- Goal: add the dedicated browser entry point for profile updates and anchor it from the existing profile view.
- Dependencies: approved Step 2; existing profile summary/rendering flow; existing compose-page layout pattern.
- Expected changes: add one dedicated route such as `/profiles/<identity-slug>/update`, introduce a focused profile-update page renderer/template that shows the current display-name context plus one editable username/display-name field, and extend `/profiles/<identity-slug>` with a clear link into that flow; planned helpers such as `renderProfileUpdatePage(summary, *, dry_run=False) -> str` and `buildProfileUpdatePageContext(summary) -> dict[str, str]`.
- Verification approach: open a known profile, confirm the new update link is visible, load the dedicated update page for a valid identity, and confirm unknown profile slugs still return the current missing-resource behavior.
- Risks or open questions:
  - choosing route and link copy that make the page feel like a signed write action rather than authenticated account settings
  - deciding how much resolved-identity context to show without turning the page into another profile read view
- Canonical components/API contracts touched: `/profiles/<identity-slug>`; new profile-update page route; shared page renderer/template contract for signed browser write flows.

## Stage 2
- Goal: extend the browser signing flow so it can build canonical `update_profile` payloads without breaking signed thread/reply compose.
- Dependencies: Stage 1; existing browser key storage/signing helpers; existing `update_profile` API contract.
- Expected changes: add profile-update form state and canonical payload generation for the minimal `set_display_name` action, pass the source identity and current page context through the new route, and lightly generalize the browser asset only where needed so one script can support both posting and profile updates; planned helpers such as `buildCanonicalProfileUpdatePayload(formState, defaults) -> { payload: string, recordId: string }`, `profileUpdateDefaults(root) -> ProfileUpdateDefaults`, and `updatePayloadPreview(formState, commandName, defaults) -> void`.
- Verification approach: load the update page with a stored or generated key, type a new display name, confirm the payload preview resolves to the expected profile-update shape, and confirm the existing signed thread/reply pages still build previews correctly.
- Risks or open questions:
  - keeping profile-update canonicalization aligned with backend validation rules for display-name normalization
  - avoiding a premature generic action framework while still extracting enough shared client logic to prevent obvious duplication
- Canonical components/API contracts touched: `browser_signing.js`; local key generation/import/storage; canonical `update_profile` payload shape and preview behavior.

## Stage 3
- Goal: complete signed submission, deterministic feedback, and readback for browser-driven username updates.
- Dependencies: Stage 2.
- Expected changes: submit signed profile updates to `/api/update_profile`, show stable success/error results in the dedicated page, and redirect successful submissions back to the canonical profile read surface so the updated name is immediately visible; planned helpers such as `submitSignedCommand(commandName, endpoint, payload, keys, dryRun) -> Promise<string>` and `redirectTarget(commandName, recordId, defaults) -> string`.
- Verification approach: submit a valid browser-driven profile update, confirm the response reports success, confirm the browser returns to the profile page with the new display name visible, and confirm signer mismatch or invalid display-name submissions return stable errors while leaving existing profile and attribution surfaces unchanged.
- Risks or open questions:
  - handling the UX clearly when the local key does not match the profile being updated and the backend rejects the request
  - choosing the smallest redirect/readback behavior that proves success without adding extra state-management complexity
- Canonical components/API contracts touched: `/api/update_profile`; browser status/response handling for signed actions; `/profiles/<identity-slug>` as the post-submit readback surface.
