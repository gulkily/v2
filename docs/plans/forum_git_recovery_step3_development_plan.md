1. Goal: add a canonical `./forum git-recover` entrypoint and a dedicated recovery helper without bloating the existing task router.
Dependencies: approved Step 2; current wrapper in `forum`; current task runner in `scripts/forum_tasks.py`.
Expected changes: add a new `git-recover` subcommand to `./forum` and `python3 scripts/forum_tasks.py ...`; add a dedicated helper file such as `scripts/forum_git_recover.py` that exposes a narrow entry function like `run_git_recover(repo_root: Path, *, apply: bool = False) -> int`; keep `scripts/forum_tasks.py` as thin argument parsing and dispatch only.
Verification approach: run `./forum help` and confirm the new subcommand appears; run the command in a clean checkout and confirm it reports a no-op healthy state.
Risks or open questions:
- whether the first slice should default to diagnosis-only and require an explicit apply flag
- exact operator-facing command wording for status-only versus repair mode
Canonical components/API contracts touched: `./forum`; `python3 scripts/forum_tasks.py ...`; new `scripts/forum_git_recover.py`.

2. Goal: implement deterministic git-state diagnosis for only the in-scope broken states with likelihood `>= 0.1`.
Dependencies: Stage 1.
Expected changes: define one diagnosis model in the helper that classifies these states: detached `HEAD`, rebase in progress, merge in progress, missing upstream, wrong checked-out branch for deployment, branch ahead of upstream, branch behind upstream, branch diverged from upstream, pull strategy unset or incompatible, fast-forward-only pull blocked by local commits, tracked working-tree changes, staged-but-uncommitted index changes, and untracked-file obstruction; explicitly mark lower-likelihood states from Step 2 as out of scope for this feature slice.
Verification approach: create disposable repo fixtures for each targeted state and confirm the command reports the expected diagnosis and recommended action text.
Risks or open questions:
- some states overlap, so the diagnosis order must be stable and explain the primary blocker first
- untracked-file obstruction may only be discoverable when simulating checkout/reset targets rather than from `git status` alone
Canonical components/API contracts touched: `scripts/forum_git_recover.py` diagnosis output contract only.

3. Goal: add safe auto-repair behavior for clean or low-risk production recovery states.
Dependencies: Stage 2.
Expected changes: implement guided repair paths that can safely restore the target deployment state when there are no tracked local changes to preserve; planned behaviors may include reattaching local `main` to `origin/main`, repairing missing upstream, normalizing pull policy to fast-forward-only, and fast-forwarding when only behind upstream. Planned contract may include a helper like `repair_checkout(repo_root: Path, diagnosis: RepoDiagnosis, *, allow_destructive: bool = False) -> RepairResult`.
Verification approach: exercise detached-HEAD, missing-upstream, behind-upstream, wrong-branch, and pull-strategy cases in disposable repos; confirm the final state is clean local `main` tracking `origin/main`.
Risks or open questions:
- whether "wrong branch" should auto-switch only when the worktree is clean
- whether pull-policy repair belongs in every successful repair path or only when misconfigured
Canonical components/API contracts touched: `scripts/forum_git_recover.py` repair contract; deployment assumption that the desired state is local `main` tracking `origin/main`.

4. Goal: gate destructive or ambiguous recovery states behind explicit operator intent instead of silent repair.
Dependencies: Stages 2-3.
Expected changes: add refusal/confirmation behavior for ahead-of-upstream, diverged, tracked-changes, staged-changes, and untracked-obstruction states; the command should stop with deterministic guidance unless the operator explicitly opts into destructive recovery. Planned contract may include a flag such as `--force-clean` or similar, but no silent reset/stash behavior by default.
Verification approach: simulate each guarded state and confirm diagnosis succeeds, automatic repair is blocked by default, and the command prints the exact reason destructive action is required.
Risks or open questions:
- exact naming for the destructive opt-in flag
- whether ahead-of-upstream and diverged should share one guard path or produce different recovery advice
Canonical components/API contracts touched: `./forum git-recover` operator UX; `scripts/forum_git_recover.py` confirmation/exit-code behavior.

5. Goal: lock the recovery workflow into focused tests and operator documentation.
Dependencies: Stages 1-4; existing command docs in `docs/developer_commands.md`; existing CLI tests in `tests/test_forum_tasks.py`.
Expected changes: add focused tests for parser wiring, diagnosis ordering, safe-repair paths, and guarded refusal paths; update the canonical command reference with `./forum git-recover`, the supported broken states for this slice, and the intended production end state. If the command becomes part of the normal operator workflow, add a concise note to `README.md`.
Verification approach: run the focused test files and manually smoke-test the production incident path: interrupted rebase leading to detached `HEAD`, then recovery back to clean `main` tracking `origin/main`.
Risks or open questions:
- keeping the docs concise while still naming supported versus unsupported broken states
- avoiding brittle tests that depend on Git version-specific phrasing rather than repository state
Canonical components/API contracts touched: `tests/test_forum_tasks.py`; new recovery tests; `docs/developer_commands.md`; optional `README.md`.
