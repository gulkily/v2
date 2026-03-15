## Stage 1 - Canonical Instance Facts Model
- Changes:
  - Added `forum_core.instance_info` as the shared read-side contract for public instance facts.
  - Added tracked public instance metadata at `records/instance/public.txt` for instance name, admin/contact info, retention policy, install date, and summary text.
  - Derived runtime-facing facts for moderation settings, commit ID, and commit date from canonical local sources instead of templates.
- Verification:
  - Ran `python3 -m unittest tests.test_instance_info`.
  - Confirmed tracked metadata parsing, missing-value behavior, moderator allowlist summary text, and git-derived commit facts in a disposable repo fixture.
- Notes:
  - The main source-of-truth split is now explicit: tracked public metadata lives in `records/instance/public.txt`, while deploy/runtime identity facts are derived at render time.

## Stage 2 - Public Instance Info Route
- Changes:
  - Added `render_instance_info_page()` to the read-only web app and exposed a canonical `/instance/` route.
  - Added `templates/instance_info.html` to render grouped policy, operator, and deployment facts through the existing shared page shell.
  - Kept the page read-only and reused the same public rendering stack as the board index, moderation log, and thread views.
- Verification:
  - Ran a focused WSGI smoke check with `python3 -c ...` against `/instance/` in a disposable repo root.
  - Confirmed the route returned `200 OK` and rendered the instance facts section, the canonical route path, and tracked contact information.
- Notes:
  - The route currently exists without main-page navigation; discoverability is handled in Stage 3 so the route and source contract stay decoupled.
