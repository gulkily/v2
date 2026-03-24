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

## Stage 3 - Execute archive creation and guarded history rewrite
- Changes:
  - Extended `scripts/forum_content_purge.py` so `--apply` now creates the normalized zip archive, writes the external manifest, checks for `git-filter-repo`, rewrites history for the selected paths, and prints the required post-rewrite follow-up actions.
  - Added explicit helper boundaries for archive creation, manifest writing, `git-filter-repo` availability checks, history rewrite execution, and operator follow-up messaging.
  - Kept the dirty-worktree guard in front of the destructive path, with `--force` reserved as the explicit override.
- Verification:
  - Ran `python3 -m unittest tests.test_forum_content_purge tests.test_forum_tasks`; passed 29 tests.
  - Ran a disposable-repo apply smoke using a temporary `git-filter-repo` shim that rewrites history through `git filter-branch`; confirmed the archive and manifest were created, `git log --all -- records/posts/root-001.txt` returned no reachable history, and unrelated `README.md` history remained reachable.
- Notes:
  - The local machine does not need a globally installed `git-filter-repo` for tests or smoke runs, but real operator use still requires the executable to be present on `PATH`.
  - The archive and manifest are intentionally written before history rewrite so purge failures still leave the exported content behind.

## Stage 4 - Add focused automated coverage for apply-mode behavior
- Changes:
  - Extended `tests/test_forum_content_purge.py` with the missing-`git-filter-repo` failure case and a disposable-repo apply test that uses a temporary `git-filter-repo` shim to verify archive creation, manifest creation, normalized zip metadata, and rewritten history.
  - Kept the existing CLI parser/dispatch coverage in `tests/test_forum_tasks.py` aligned with the helper changes from earlier stages.
- Verification:
  - Ran `python3 -m unittest tests.test_forum_content_purge tests.test_forum_tasks`; passed 31 tests.
  - Ran `python3 scripts/forum_tasks.py content-purge records/posts --apply --archive-output /tmp/content-purge-apply.zip` in the current checkout and confirmed the dirty-worktree guard stops the destructive path before archive creation or history rewriting.
- Notes:
  - The current checkout remains intentionally dirty because of unrelated local work, so the direct `./forum` apply smoke here is expected to stop at the safety gate.
  - The disposable-repo test is now the automated proof that the apply path can complete when the repo is clean and `git-filter-repo` is available on `PATH`.

## Stage 5 - Document the operator workflow and prerequisites
- Changes:
  - Updated `docs/developer_commands.md` with the new `./forum content-purge` command, preview/apply examples, supported selection scope, safety guards, `git-filter-repo` prerequisite, and required post-rewrite follow-up actions.
  - Updated `README.md` so the command is discoverable from the top-level common-command list and operator-cleanup guidance.
  - Updated `records/README.md` to point operators at `./forum content-purge` as the canonical cleanup path for record-family history purges.
- Verification:
  - Re-read the updated `README.md`, `docs/developer_commands.md`, and `records/README.md` flow to confirm the command can be discovered from the top-level docs, followed to preview/apply examples, and tied back to the canonical `records/` tree.
- Notes:
  - The docs intentionally keep the workflow framed as operator-only destructive maintenance rather than casual content cleanup.
