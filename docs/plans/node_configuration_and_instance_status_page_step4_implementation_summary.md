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
