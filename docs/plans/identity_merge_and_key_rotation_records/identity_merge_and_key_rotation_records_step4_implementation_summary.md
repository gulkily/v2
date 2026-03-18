## Stage 1 - identity-link records and deterministic resolution helpers
- Changes:
  - Added a shared identity-link helper module for canonical `rotate_key` and `merge_identity` record parsing, detached sidecar discovery, and deterministic linked-identity resolution.
  - Defined one canonical records directory for identity links under `records/identity-links/` and documented it alongside the existing post, bootstrap, and moderation record families.
  - Chose deterministic activation rules for the first slice: `rotate_key` links one visible identity to a not-yet-visible key-backed alias, while `merge_identity` only becomes active when reciprocal visible assertions exist.
- Verification:
  - Compiled the new helper layer with `python3 -m py_compile forum_core/*.py`.
  - Confirmed a merge-plus-rotation fixture resolves to one canonical linked set with a stable lexicographic canonical identity ID.
- Notes:
  - This stage intentionally stopped short of exposing a write route or changing any profile/read behavior.

## Stage 2 - signed identity-link write contract
- Changes:
  - Added a signed `link_identity` write contract with detached-signature verification, canonical text storage under `records/identity-links/`, and git-backed commits.
  - Added deterministic plain-text preview and success serializers for identity-link writes.
  - Exposed the write contract through `/api/link_identity` and listed it on the API home surface.
  - Kept authority rules intentionally narrow for this loop: the signer must match `Source-Identity-ID`, `merge_identity` targets must already be visible identities, and `rotate_key` targets must not already be visible or previously linked.
- Verification:
  - Compiled the updated modules with `python3 -m py_compile forum_cgi/*.py forum_core/*.py forum_read_only/*.py`.
  - In a disposable repository clone, created two visible signed identities, then confirmed signed `rotate_key` and `merge_identity` records store payload, signature, and public-key sidecars under `records/identity-links/` and produce git commits.
  - Confirmed `/api/link_identity` returns a stable dry-run preview.
  - Confirmed signer/source mismatch returns `403 Forbidden` and attempting to rotate into an already-visible identity returns `409 Conflict`.
- Notes:
  - Browser UX for merge/rotation management remains out of scope; this slice is API/CLI-first.

## Stage 3 - resolved profile and attribution updates
- Changes:
  - Extended the profile model so `get_profile` and the web profile page resolve linked identities to one canonical logical profile instead of treating each fingerprint-derived identity as final.
  - Added one shared identity context loader that combines visible bootstraps, visible signed posts, and visible identity-link records into a deterministic resolution map.
  - Updated signed post attribution and moderation attribution to link to the canonical resolved profile target rather than the raw signer-derived identity ID.
  - Updated the profile surface to show linked member identities while preserving the visible bootstrap anchor used for the current profile summary.
- Verification:
  - Compiled the updated modules with `python3 -m py_compile forum_cgi/*.py forum_core/*.py forum_read_only/*.py`.
  - In a fresh disposable repository clone, created visible `alpha` and `beta` identities, linked `alpha -> gamma` with `rotate_key`, created reciprocal `merge_identity` records between `alpha` and `beta`, and then created a visible signed `gamma` post.
  - Confirmed `/api/get_profile` requested through both `alpha` and `gamma` aliases returns identical text with one canonical `Identity-ID`, `Member-Identity-Count: 3`, and all visible linked posts.
  - Confirmed `/profiles/<alpha-slug>` returns `200 OK` and renders the canonical resolved profile.
  - Confirmed post pages for both `alpha-thread` and `gamma-thread` link to the canonical resolved profile slug rather than their raw signer-derived identity IDs.
  - Confirmed a moderation record signed by `beta` links to the same canonical resolved profile on `/moderation/`.
- Notes:
  - Moderator-trusted merge assertions, richer merge conflict policy, and display-name editing remain separate future loops.
