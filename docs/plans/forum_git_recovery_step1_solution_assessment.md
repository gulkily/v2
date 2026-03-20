# Forum Git Recovery Step 1: Solution Assessment

## Problem Statement
Operators can leave a deployed checkout in a broken git state during `git pull` recovery, so `./forum` needs a safe, canonical way to detect and repair common deployment-sync failures such as detached `HEAD`, interrupted rebases, and divergent local `main`.

## Option A: Add one `./forum git-recover` command that inspects repo state and applies a guided safe recovery path
- Pros:
  - Keeps operator recovery inside the repo's canonical command surface.
  - Can encode repo-specific rules such as "production should track `origin/main`" and "prefer fast-forward-only pulls".
  - Can detect several related failure states in one place: detached `HEAD`, rebase/merge in progress, missing upstream, dirty worktree, or local branch divergence.
  - Gives room for a dry-run/status mode and clear operator messaging instead of raw git errors.
- Cons:
  - Needs careful guardrails so it does not discard meaningful local work by default.
  - Slightly larger initial command design because it combines diagnosis and repair.

## Option B: Add a narrower `./forum deploy-sync` command that only force-aligns production checkouts to `origin/main`
- Pros:
  - Smallest implementation for the production-server case.
  - Easy to document as the standard post-pull recovery command for deployments.
  - Lower decision surface because it assumes one desired end state.
- Cons:
  - Too narrow for similar local operator failures outside the exact production workflow.
  - Risks becoming a wrapper around destructive reset behavior without enough diagnosis.
  - Leaves other broken states to ad hoc manual git commands.

## Option C: Keep recovery in docs only and standardize a manual git runbook
- Pros:
  - No code changes.
  - Full flexibility for experienced operators.
- Cons:
  - Repeats the current failure mode: operators must interpret git state correctly under pressure.
  - Easy to misuse on a live deployment, especially around rebase, detached `HEAD`, and branch/upstream repair.
  - Misses the stated goal of making `./forum` handle this class of issue automatically.

## Recommendation
Recommend Option A: add a `./forum git-recover` command that first diagnoses the checkout state, then applies the smallest safe repair path for known deployment-sync failures.

This is the best fit because the problem is not just one broken `git pull`; it is a recurring class of operator recovery mistakes. A diagnosis-first recovery command keeps the solution inside `./forum`, covers the production incident directly, and can extend to adjacent git-state failures without turning recovery into undocumented shell folklore.
