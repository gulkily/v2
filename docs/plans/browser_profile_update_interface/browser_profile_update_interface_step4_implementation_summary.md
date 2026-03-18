## Stage 1 - profile update entry point and dedicated page shell
- Changes:
  - Added a clear `update username` action link to the existing profile page so the browser flow is discoverable from the canonical read surface.
  - Added a dedicated `/profiles/<identity-slug>/update` page with resolved identity context, a focused display-name field, and placeholder form structure for the later browser-signing stages.
  - Added route handling plus focused smoke tests for the new profile-update page.
- Verification:
  - Ran `python3 -m unittest discover -s tests -p 'test_profile_update_page.py'` and confirmed the profile page links to the update flow and the dedicated update page renders the expected identity context.
  - Ran `python3 -m unittest discover -s tests -p 'test_compose_reply_page.py'` to confirm the existing reply compose page still renders correctly.
  - Ran `python3 -m py_compile forum_read_only/web.py`.
- Notes:
  - The page shell is intentionally static at this stage; the browser signing asset is wired in Stage 2.

## Stage 2 - browser signing support for canonical profile-update previews
- Changes:
  - Extended the dedicated profile-update page to reuse the existing browser signing shell, including key import/generation controls, canonical payload preview, detached-signature preview, and response output panes.
  - Generalized `browser_signing.js` so it can build canonical `update_profile` payloads for `set_display_name` without regressing signed thread and reply composition.
  - Added profile-update-specific key handling so the page reuses an existing stored key when present and asks for an import when no matching local key is available instead of silently auto-generating one on load.
- Verification:
  - Ran `python3 -m unittest discover -s tests -p 'test_profile_update_page.py'`.
  - Ran `python3 -m unittest discover -s tests -p 'test_compose_reply_page.py'`.
  - Ran `python3 -m py_compile forum_read_only/web.py`.
  - Ran `node --input-type=module --eval "import('node:fs/promises').then(async (fs) => { let source = await fs.readFile('templates/assets/browser_signing.js', 'utf8'); source = source.replace(/^import .*$/m, 'const openpgp = {};').replace(/main\\(\\);\\s*$/, ''); await import('data:text/javascript,' + encodeURIComponent(source)); console.log('browser_signing.js parsed'); });"` and confirmed the browser module parses after stubbing the top-level import and `main()` call for a non-browser syntax smoke check.
- Notes:
  - The update page currently submits deterministic dry-run previews only; Stage 3 will switch it to real `update_profile` submissions and redirect back to the profile read surface.

## Stage 3 - real browser profile-update submission and readback
- Changes:
  - Switched the dedicated profile-update page from dry-run preview mode to real signed submission mode and updated the page copy to reflect repository-backed writes.
  - Reused the shared browser signing asset so successful `update_profile` submissions now post to `/api/update_profile` and redirect back to the canonical profile page.
  - Added an end-to-end test that generates a browser-style OpenPGP key, signs a canonical profile-update payload, submits it through the WSGI app, and confirms the updated display name appears on the profile read surface.
- Verification:
  - Ran `python3 -m unittest discover -s tests -p 'test_profile_update_submission.py'`.
  - Ran `python3 -m unittest discover -s tests -p 'test_profile_update_page.py'`.
  - Ran `python3 -m unittest discover -s tests -p 'test_compose_reply_page.py'`.
  - Ran `python3 -m py_compile forum_read_only/web.py`.
- Notes:
  - The update flow still depends on a matching local or imported private key for the profile being edited; there is still no broader account-session model in this slice.
