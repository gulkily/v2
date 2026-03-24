## Stage 1 - Add CLI entrypoint and preview helper boundary
- Changes:
  - Added `content-purge` to the canonical `./forum` / `python3 scripts/forum_tasks.py ...` command surface.
  - Added `scripts/forum_content_purge.py` as a dedicated helper boundary for the future archival-and-history-rewrite workflow.
  - Kept Stage 1 preview-only: the helper prints the selected paths, optional archive output path, and non-mutating status instead of attempting archive creation or history rewriting.
  - Added parser and dispatch coverage for the new command in `tests/test_forum_tasks.py`.
- Verification:
  - Ran `python3 -m unittest tests.test_forum_tasks`; passed 23 tests.
  - Ran `./forum help` and confirmed `content-purge` appears in the canonical CLI help output.
  - Ran `python3 scripts/forum_tasks.py content-purge records/posts records/identity` and confirmed it prints a preview with the selected paths and an explicit no-mutation message.
- Notes:
  - `--apply`, `--archive-output`, and `--force` are present in the Stage 1 command shape so later stages can extend behavior without renaming the operator surface.
  - Real path validation, archive generation, and history rewriting remain for later stages.

## Stage 2 - Add path validation, archive planning, and preview contract
- Changes:
  - Expanded `scripts/forum_content_purge.py` with a real planning layer that resolves canonical `records/` paths, rejects non-`records/` targets, rejects overlapping selections, and gathers the archived file set.
  - Added archive/manifest planning output, including default archive-path derivation outside the repo root plus head and oldest reachable commit anchors for the purge manifest.
  - Added a reusable manifest-rendering helper and dirty-worktree refusal behavior for future apply mode.
  - Added focused helper coverage in `tests/test_forum_content_purge.py` for valid selection, invalid selection, overlap refusal, preview output, manifest contents, and dirty-worktree refusal.
- Verification:
  - Ran `python3 -m unittest tests.test_forum_content_purge tests.test_forum_tasks`; passed 29 tests.
  - Ran `python3 scripts/forum_tasks.py content-purge records/posts records/identity --archive-output /tmp/content-purge-preview.zip` and confirmed the preview reports archive/manifest outputs, commit anchors, and archived file count without creating files or mutating history.
- Notes:
  - Archive output is now required to live outside the repository root so the workflow does not dirty the repo with its own export artifacts.
  - Apply mode still stops before archive creation or history rewriting; Stage 3 will execute the planned workflow once the guardrails are in place.
