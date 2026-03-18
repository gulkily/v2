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

## Stage 3 - Board Index Discoverability
- Changes:
  - Added an `instance info` action to the main board-index action row in `templates/board_index.html`.
  - Kept the link on the existing primary public navigation surface so the page is visible in one click without adding a new global navigation system.
- Verification:
  - Ran a focused WSGI smoke check with `python3 -c ...` against `/`.
  - Confirmed the board index returned `200 OK`, rendered the `instance info` label, and linked directly to `/instance/`.
- Notes:
  - The board-index action row now carries four primary public destinations; the wording stays intentionally technical to match the feature’s audience.

## Stage 4 - Tests And Operator Docs
- Changes:
  - Added `tests/test_instance_info_page.py` to cover the board-index link, the `/instance/` route, rendered public fact fields, and missing-metadata placeholders.
  - Updated `docs/developer_commands.md` to document the canonical source of public instance metadata and which facts are derived at render time.
- Verification:
  - Ran `python3 -m unittest tests.test_instance_info tests.test_instance_info_page`.
  - Confirmed 7 focused tests passed for helper parsing, git-derived facts, page rendering, board-index discoverability, and explicit missing-value behavior.
- Notes:
  - The test run emits the existing missing-`.env` reminder from startup; that warning is expected and does not affect the instance-info feature behavior.
