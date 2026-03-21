## Problem Statement
Choose the safest operator workflow for exporting repository-backed content into an archive and then removing that content from the git repository, including past commits, so future operators can reset the repository to a clean baseline instead of carrying forward development or test content.

### Option A: Add an archive script that zips the content and deletes it only from the current tree
- Pros:
  - Smallest implementation effort.
  - Easy to test because it only needs to collect files, write a zip, and remove the selected paths from the working tree.
  - Avoids history rewriting and the operational coordination that comes with force-pushing a rewritten repository.
- Cons:
  - Does not satisfy the requirement to strip content from git history.
  - Leaves all historical content recoverable through old commits, tags, and existing clones.
  - Risks creating false confidence because the repo looks scrubbed while the history still contains the data.

### Option B: Add an operator-only script that creates a normalized archive and then rewrites repository history with `git filter-repo`
- Pros:
  - Best match for the requested outcome because it handles both export and historical removal in one operator-focused workflow for future clean-start resets.
  - Can target the canonical content paths directly, such as `records/posts/`, `records/identity/`, and other operator-selected record directories.
  - `git filter-repo` is the modern, reliable way to rewrite git history compared with older `filter-branch` approaches.
  - A script can enforce guardrails such as clean-worktree checks, explicit path selection, archive manifests, dry-run mode, and prominent warnings before force-push steps.
- Cons:
  - Higher operational risk than ordinary feature work because rewriting history affects remotes, tags, cached clones, and any downstream users.
  - Requires an additional dependency or documented prerequisite if `git filter-repo` is not already installed in the operator environment.
  - “Including history” is not purely a local code change; success also depends on coordinated follow-through after the script runs, including force-push, mirror cleanup, and clone rotation.

### Option C: Export the content, then create a fresh repository or orphan-history reset instead of selectively rewriting history
- Pros:
  - Simpler mental model than selective history surgery.
  - Guarantees the new repository history is clean if the operator migrates only the retained files.
  - May be faster for a one-time full reset if preserving commit history is not important.
- Cons:
  - Much more disruptive to normal development because all prior non-content history is lost or split away.
  - Changes repository identity and complicates links, forks, automation, and deployment assumptions.
  - Larger blast radius than the stated goal, which is to strip content while preserving the rest of the repo where possible.

## Recommendation
Recommend Option B: add an operator-only archival-and-history-rewrite script built around `git filter-repo`.

This is not especially difficult from an implementation standpoint, but it is operationally sensitive. The hard part is not zipping files; it is rewriting history safely and making sure the purge is real across remotes and old clones. Because the goal is to give future operators a repeatable way to restore the repository to a clean baseline, the workflow should be explicit about both the archival output and the required post-rewrite cleanup steps. A good script can make the mechanical portion straightforward by:

- collecting selected content paths into one normalized zip archive, with any timestamp kept in the filename or manifest rather than in the archive contents
- writing a manifest that records which paths and commit range were archived
- refusing to run on a dirty worktree unless explicitly overridden
- offering a dry-run mode before any destructive step
- invoking `git filter-repo` to remove the archived paths from all reachable history
- printing the required next actions such as force-pushing rewritten refs and rotating old clones

So the honest answer is: implementation difficulty is moderate, but operational risk is high. That is exactly the kind of feature where Step 1 is useful, and the safest path is a tightly scoped operator workflow rather than a casual utility command.
