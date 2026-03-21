1. Goal: add one canonical `./forum` purge entrypoint and a dedicated helper boundary for archival-plus-history-rewrite work.
Dependencies: approved Step 2; current wrapper in `forum`; current task runner in `scripts/forum_tasks.py`; existing operator command docs in `docs/developer_commands.md`.
Expected changes: add a new operator-facing subcommand to `./forum` and `python3 scripts/forum_tasks.py ...`; add a focused helper module such as `scripts/forum_content_purge.py` with a narrow entry function like `run_content_purge(repo_root: Path, *, paths: list[str], archive_output: Path | None = None, dry_run: bool = False, force: bool = False) -> int`; keep the task runner as thin parsing and dispatch only; no database changes.
Verification approach: run `./forum help` and confirm the new subcommand appears; run the command with a preview-only invocation in a clean checkout and confirm it reports the selected path set without mutating history.
Risks or open questions:
- Confirm the final command name and flag set before implementation so operator docs and tests do not churn.
- Keep the wrapper/task-runner change small so purge logic does not leak into parser code.
Canonical components/API contracts touched: `./forum`; `python3 scripts/forum_tasks.py ...`; new purge helper module only.

2. Goal: define the archive-selection, manifest, and safety-check contract before any history rewrite runs.
Dependencies: Stage 1; current canonical `records/` tree; existing record-family docs such as `records/README.md`.
Expected changes: add helper logic that resolves and validates operator-selected canonical `records/` paths, refuses unsafe or ambiguous selections, checks for a clean worktree unless explicitly overridden, and defines the normalized archive plus manifest output contract; planned helper boundaries may include `resolve_purge_paths(repo_root: Path, requested_paths: list[str]) -> list[Path]`, `build_archive_manifest(...) -> str`, and `create_normalized_archive(...) -> Path`; no database changes.
Verification approach: in a disposable repo or fixture tree, preview a valid selection and confirm the reported archive inputs and manifest details are stable; preview invalid selections and confirm the command refuses paths outside the intended canonical content areas.
Risks or open questions:
- Decide whether the first slice accepts any `records/` family or a narrower allowlist such as posts/identity/profile updates only.
- Archive normalization rules must be explicit enough that repeated operator runs are predictable.
Canonical components/API contracts touched: canonical `records/` path-selection contract; archive manifest output contract only.

3. Goal: add the guarded history-rewrite execution path for the approved archive selection.
Dependencies: Stages 1-2; local git checkout; operator prerequisite for `git filter-repo`.
Expected changes: extend the purge helper so non-dry-run execution creates the archive/manifest, invokes `git filter-repo` against the selected paths, and prints required post-run actions for force-push, remote cleanup, and clone rotation; planned helper boundaries may include `ensure_filter_repo_available() -> None`, `rewrite_history(repo_root: Path, paths: list[str]) -> None`, and `render_post_rewrite_instructions(...) -> str`; no database changes.
Verification approach: in a disposable repository clone, run the real purge flow against sample `records/` paths and confirm the archive exists, reachable history no longer contains the selected files, and the command emits the expected follow-up instructions.
Risks or open questions:
- `git filter-repo` availability and error handling need to be explicit so operators do not get halfway through the workflow with unclear failures.
- History rewrites can invalidate local clones and tags even when the local command succeeds; the output contract must make that risk unmistakable.
Canonical components/API contracts touched: purge command execution contract; local git history rewrite contract only.

4. Goal: cover the operator guardrails and destructive-flow messaging with focused automated tests.
Dependencies: Stages 1-3; existing CLI test patterns in `tests/test_forum_tasks.py`; disposable-repo test helpers already used for git-backed features.
Expected changes: add parser/dispatch coverage for the new subcommand, targeted helper tests for valid and invalid path selection, clean-worktree refusal, dry-run output, missing-`git filter-repo` handling, and successful disposable-repo purge flow; no database changes.
Verification approach: run the targeted unittest files covering the CLI parser and purge helper behavior; manually spot-check one disposable-repo purge run to confirm automated expectations still match the operator-facing output.
Risks or open questions:
- Full history-rewrite tests must stay isolated and fast enough to remain practical in the normal suite.
- Tests should assert operator-visible warnings and next-step guidance, not only low-level helper return values.
Canonical components/API contracts touched: `tests/test_forum_tasks.py`; new purge workflow tests; operator-visible CLI output contract.

5. Goal: document the purge workflow, prerequisites, and operator follow-through in the canonical command references.
Dependencies: Stages 1-4; existing operator docs in `docs/developer_commands.md`, `README.md`, and `records/README.md`.
Expected changes: document the new `./forum` purge command, required `git filter-repo` prerequisite, supported path-selection scope, dry-run expectation, archive/manifest outputs, and mandatory post-rewrite operator actions; update repo docs only where this workflow should become part of the standard operator baseline; no database changes.
Verification approach: read the updated command/docs flow from top to bottom and confirm an operator can discover prerequisites, run the preview path, execute the purge, and finish the required follow-up actions without reading implementation code.
Risks or open questions:
- Avoid presenting the workflow as casual cleanup; documentation must keep the destructive nature prominent.
- If the supported path scope is intentionally narrow in Stage 2, the docs must state that limitation clearly.
Canonical components/API contracts touched: `docs/developer_commands.md`; `README.md`; `records/README.md`; `./forum` operator documentation contract.
