## Stage 1 - profile-update records and deterministic display-name helpers
- Changes:
  - Added a shared profile-update helper module for canonical `set_display_name` parsing, detached sidecar discovery, and deterministic current-name resolution across linked identities.
  - Defined one canonical records directory for profile updates under `records/profile-updates/` and documented it alongside the existing post, bootstrap, identity-link, and moderation record families.
  - Chose a narrow first-slice record shape built around `Source-Identity-ID`, a single-line ASCII display name, and a deterministic latest-visible-update-wins rule keyed by timestamp and record ID.
- Verification:
  - Compiled the helper layer with `python3 -m py_compile forum_core/*.py`.
  - Parsed sample profile-update payloads and confirmed repeated resolution across member identities returns the same latest shared display name.
- Notes:
  - This stage intentionally stopped short of exposing a write route or changing any profile/read behavior.

## Stage 2 - signed profile-update write contract
- Changes:
  - Added a signed `update_profile` write contract with detached-signature verification, canonical text storage under `records/profile-updates/`, and git-backed commits.
  - Added deterministic plain-text preview and success serializers for profile updates, including the resolved signer identity and requested display name.
  - Exposed the write contract through `/api/update_profile` while keeping browser profile-management UX out of scope for this loop.
  - Kept the authority rule intentionally narrow for the first slice: the signer must match `Source-Identity-ID`, and that source identity must already resolve in the current linked-identity graph.
- Verification:
  - Compiled the updated modules with `python3 -m py_compile forum_cgi/*.py forum_core/*.py forum_read_only/*.py`.
  - In a disposable repository clone, generated temporary signing keys, created a signed bootstrap post, then confirmed valid signed `update_profile` submissions create canonical profile-update payload, detached signature, public-key sidecar, and git commit output.
  - Confirmed `/api/update_profile` returns a stable dry-run preview through the WSGI application.
  - Confirmed signer/source mismatch returns `403 Forbidden` with the expected plain-text error.
- Notes:
  - The route exists for API and CLI-style use now, but profile discovery text and read surfaces remain unchanged until later stages.

## Stage 3 - resolved profile summaries with display names
- Changes:
  - Extended the profile summary model so `get_profile` now includes `Display-Name`, `Display-Name-Source`, `Fallback-Display-Name`, and optional profile-update provenance fields.
  - Updated the shared identity context loader to read visible profile-update records alongside bootstraps and identity links.
  - Resolved the current display name across all member identities in a linked set while preserving the existing fingerprint-derived fallback label when no visible update exists.
- Verification:
  - Compiled the updated modules with `python3 -m py_compile forum_cgi/*.py forum_core/*.py forum_read_only/*.py`.
  - In a disposable repository clone, generated two signed identities, merged them with reciprocal `merge_identity` records, confirmed the pre-update profile summary still reports `Display-Name-Source: fingerprint_fallback`, then submitted a signed profile update from one member identity.
  - Confirmed `render_api_get_profile(...)` returns `200 OK` for both merged aliases and that both responses include the same updated display name, fallback field, and display-name record metadata.
- Notes:
  - The HTML profile page and attribution labels still use the old fingerprint shorthand at this stage; those surfaces are updated in Stage 4.
