## Problem
Operators currently recover broken deploy-checkout git states by hand, which makes common failures during `git pull` repair easy to worsen. The next slice should add one canonical `./forum` recovery path that can diagnose and safely resolve the full set of repo-local broken states we expect on deployed or operator-managed checkouts.

## User Stories
- As an operator, I want one `./forum` command to tell me exactly what git state is broken so that I do not have to infer recovery steps from raw git errors.
- As an operator, I want the command to repair common deploy-sync failures safely so that a production checkout can get back to tracking `origin/main` without ad hoc git surgery.
- As a maintainer, I want the recovery scope to be explicit and exhaustive for repo-local states so that we know which failures are auto-fixable, which are diagnose-only, and which remain out of scope.
- As a maintainer, I want the command to preserve meaningful local work by default so that recovery tooling does not silently destroy commits or staged changes.

## Core Requirements
- The feature must add one canonical `./forum` git-recovery surface that diagnoses the current checkout state before proposing or applying repairs.
- The feature may implement the recovery logic in a dedicated helper file so the existing command-router file does not grow into an oversized mixed-responsibility script.
- The feature must define an exhaustive in-scope broken-state inventory for repo-local git states it can address: detached `HEAD`; rebase in progress; merge in progress; cherry-pick in progress; revert in progress; bisect in progress; missing or incorrect upstream; wrong checked-out branch for deployment; branch ahead of upstream; branch behind upstream; branch diverged from upstream; fast-forward-only pull blocked by local commits; pull blocked because pull strategy is unset or incompatible; tracked working-tree changes; staged-but-uncommitted index changes; untracked-file obstruction; and unborn or missing local `main` when `origin/main` exists.
- The feature must distinguish safe auto-repair states from states that require explicit operator confirmation, especially when local commits or uncommitted tracked changes would be discarded or sidelined.
- The feature must define the production-safe target end state as a clean local `main` attached to `origin/main` with pull behavior configured to avoid future accidental merge-or-rebase surprises.
- The feature must explicitly exclude non-repo-local failures such as network outage, remote auth failure, missing remote repository permissions, or upstream branch deletion, while still allowing the command to report those conditions clearly if encountered during diagnosis.

## Broken State Inventory
- Detached `HEAD` after reset, checkout, or interrupted rebase. Likelihood: `0.55`
- Rebase in progress with conflicts resolved or unresolved. Likelihood: `0.30`
- Merge in progress after a conflicted pull or merge attempt. Likelihood: `0.18`
- Cherry-pick in progress. Likelihood: `0.05`
- Revert in progress. Likelihood: `0.04`
- Bisect in progress. Likelihood: `0.02`
- Missing upstream for the current branch. Likelihood: `0.20`
- Incorrect upstream for the current branch. Likelihood: `0.08`
- Wrong checked-out branch for deployment, such as a feature branch instead of `main`. Likelihood: `0.22`
- Local branch ahead of upstream because of local-only commits. Likelihood: `0.16`
- Local branch behind upstream and not yet fast-forwarded. Likelihood: `0.85`
- Local branch diverged from upstream. Likelihood: `0.25`
- `git pull` blocked because pull strategy is unset or incompatible with the current state. Likelihood: `0.28`
- Fast-forward-only pull blocked by local commits. Likelihood: `0.12`
- Tracked working-tree changes present. Likelihood: `0.24`
- Staged-but-uncommitted index changes present. Likelihood: `0.14`
- Untracked files obstruct checkout, reset, or merge steps. Likelihood: `0.10`
- Unborn or missing local `main` while `origin/main` exists. Likelihood: `0.03`

Likelihood notes:
- `1.0` means "common enough to assume operators will hit it regularly" rather than "certain on every checkout."
- These values are rough planning estimates for operator-managed deploy checkouts, not measured production telemetry.
- Remote/network/auth failures remain out of scope for auto-repair even though the command may still surface them during diagnosis.

## Shared Component Inventory
- `./forum`: extend the canonical operator command wrapper with the recovery entrypoint rather than introducing a separate shell script.
- `python3 scripts/forum_tasks.py ...`: extend the existing task-runner command surface so direct and wrapped invocation stay aligned, but keep it as a thin parser/dispatcher rather than the home for all recovery logic.
- New dedicated recovery helper such as `scripts/forum_git_recover.py`: add one focused implementation file to own git-state diagnosis and repair behavior so the command router stays short and single-purpose.
- Existing operator docs in `README.md`: extend the current setup and command guidance only if the new recovery command becomes part of the documented operator workflow.
- Existing operator reference in `docs/developer_commands.md`: extend the canonical command reference with the recovery command and its intended production use.
- Existing deployment workflow contract around `origin/main`: reuse the current repo assumption that deployed checkouts should track the remote `main` branch rather than inventing a second deployment branch model.

## Simple User Flow
1. An operator runs the new `./forum` git-recovery command from a deployed or local checkout that is failing normal `git pull`.
2. The command reports the detected git state, including whether the checkout is detached, mid-operation, dirty, mis-tracking upstream, or diverged from `origin/main`.
3. The command either applies the safe repair path automatically or stops with a clear confirmation/error message when local work would be affected.
4. After recovery, the checkout is back on local `main`, tracks `origin/main`, has a clean working tree, and uses the intended pull behavior for future updates.

## Success Criteria
- An operator can run one `./forum` command and get a deterministic diagnosis for any in-scope repo-local broken state.
- The feature documentation names the full in-scope broken-state inventory and separates it from out-of-scope remote/network failures.
- The command can return a broken production checkout to clean `main` tracking `origin/main` for the common failure cases represented by detached `HEAD`, interrupted git operations, upstream misconfiguration, and branch divergence.
- The command does not silently discard local commits or tracked working-tree changes; states with destructive implications require explicit operator intent.
- After a successful recovery, future `git pull` behavior is predictable and does not depend on Git's default merge-vs-rebase prompt behavior.
