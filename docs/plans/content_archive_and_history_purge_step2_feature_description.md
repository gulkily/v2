## Problem
The repository can accumulate development and test content under the canonical `records/` tree, which leaves future operators without a clean baseline to start from. The next slice should define one operator-only workflow that archives selected repository-backed content and removes it from all reachable git history so the repo can be reset cleanly without abandoning the rest of its commit history.

## User Stories
- As an operator, I want one documented cleanup workflow that archives selected `records/` content before purging it so that I can preserve the old data outside the repo.
- As a future operator, I want the workflow to remove the selected content from reachable git history so that a fresh clone starts from a genuinely clean baseline.
- As a maintainer, I want the purge flow to make destructive implications explicit so that history rewrites are deliberate rather than casual cleanup steps.
- As a reviewer, I want the workflow to reuse the repository's canonical record layout and operator command surfaces so that cleanup behavior stays discoverable and consistent with the rest of the project.

## Core Requirements
- The feature must define one operator-only workflow that archives operator-selected canonical content paths and then removes those paths from all reachable git history.
- The workflow must target content stored under the existing `records/` tree, including paths such as `records/posts/`, `records/identity/`, and other operator-selected record families.
- The workflow must produce a normalized archive plus a manifest describing what was archived so the exported content remains inspectable after the purge.
- The workflow must require explicit guardrails before destructive history changes, including a preview path and clear follow-up instructions for force-push, clone rotation, and related cleanup outside the local checkout.
- The workflow must preserve the rest of the repository history where possible rather than replacing the repo with an orphan-history reset or fresh repository.

## Shared Component Inventory
- Existing canonical data surface: reuse the current `records/` repository layout as the source of truth for path selection rather than introducing a second content inventory.
- Existing operator command surface: prefer the canonical project command entrypoint for operator workflows so the purge flow does not become an undocumented standalone utility.
- Existing operator documentation: extend the command and operator references in `README.md` and `docs/developer_commands.md` so the purge workflow and its prerequisites are discoverable.
- Existing repository record docs: reuse `records/README.md` and the current record-family documentation to describe which canonical content paths are eligible for archival and purge.

## Simple User Flow
1. An operator chooses one or more canonical `records/` paths to remove from the repository's historical content set.
2. The operator runs the purge workflow and reviews a preview of the selected paths, archive output, and destructive follow-up steps.
3. The workflow creates the archive and manifest for the selected content.
4. The workflow removes the selected paths from reachable git history and reports the required remote-cleanup actions.
5. The operator completes the documented follow-up steps so future clones start from the cleaned repository history.

## Success Criteria
- An operator can archive selected canonical `records/` content without manually collecting files.
- The workflow removes the selected paths from reachable git history while preserving unrelated repository history.
- The workflow makes destructive consequences and required post-rewrite actions explicit before the operator proceeds.
- A future operator can follow the documented process and obtain a fresh clone that no longer contains the purged content in normal reachable history.
- The cleanup flow is documented through the project's existing operator command and reference surfaces rather than living as tribal knowledge.
