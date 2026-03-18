## Stage 1 - identity bootstrap and profile helpers
- Changes:
  - Added a shared identity helper module for public-key fingerprint derivation, stable `Identity-ID` construction, bootstrap payload building, and deterministic plain-text profile serialization.
  - Extended canonical post loading so signed posts now carry derived identity metadata from their stored public-key sidecars.
  - Kept the helper layer separate from the write and read routes so later stages could reuse one identity model instead of duplicating logic.
- Verification:
  - Compiled the new modules with `python3 -m py_compile forum_core/*.py forum_read_only/repository.py`.
  - Loaded the current repository posts and confirmed signed sample posts derive a stable `openpgp:<fingerprint>` identity ID from their public-key sidecars.
- Notes:
  - This stage intentionally stopped short of creating bootstrap records or exposing profile routes.

## Stage 2 - automatic bootstrap on first signed post
- Changes:
  - Extended the signed posting service so the first signed post for a key now creates a deterministic identity bootstrap record under `records/identity/` in the same git-backed write flow.
  - Added identity reporting to signed write responses: `Identity-ID`, `Identity-Bootstrap-Path`, and whether bootstrap material was created on that request.
  - Reused the existing detached-signature verification path so bootstrap creation is driven by verified key material rather than a separate registration mechanism.
- Verification:
  - Submitted two signed threads with the same newly generated key against a disposable repository clone while importing the in-progress working tree code.
  - Confirmed the first signed post created `records/identity/identity-openpgp-<fingerprint>.txt` and reported `Identity-Bootstrap-Created: yes`.
  - Confirmed the second signed post reused the same `Identity-ID` and bootstrap path and reported `Identity-Bootstrap-Created: no`.
- Notes:
  - Bootstrap material is committed alongside the first signed post, so identity creation is automatic and transparent to the browser user.

## Stage 3 - get_profile and profile view
- Changes:
  - Added a plain-text `get_profile` read surface and exposed it through `/api/get_profile?identity_id=<identity-id>`.
  - Added a read-only profile page at `/profiles/<identity-slug>` and linked signed posts to that profile surface.
  - Added profile-summary derivation that prefers explicit bootstrap records and falls back to synthetic bootstrap material from older signed posts, so the current dataset is immediately browsable without manual backfill.
  - Updated the API home text so `get_profile` is listed as a first-class command.
- Verification:
  - Compiled the updated modules with `python3 -m py_compile forum_cgi/*.py forum_core/*.py forum_read_only/*.py`.
  - Confirmed the current signed sample posts derive a profile summary with `summary_post_count = 6` and a synthetic bootstrap path under `records/posts/*.txt.pub.asc`.
  - Confirmed `render_api_get_profile("openpgp:708d998dd7e6b6bd05629b49676741195b215305")` returns `200 OK`.
  - Confirmed WSGI requests to `/api/`, `/api/get_profile?identity_id=openpgp:708d998dd7e6b6bd05629b49676741195b215305`, and `/profiles/openpgp-708d998dd7e6b6bd05629b49676741195b215305` all return `200 OK`.
  - Confirmed signed post pages now include a `/profiles/...` link.
- Notes:
  - Username and display-name prompts remain out of scope; the first visible identity label is still derived from the key fingerprint.
