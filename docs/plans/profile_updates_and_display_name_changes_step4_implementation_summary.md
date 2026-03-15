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
