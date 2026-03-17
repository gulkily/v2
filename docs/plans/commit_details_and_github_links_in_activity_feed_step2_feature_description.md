## Problem
`/activity/` now shows repository commits in one filtered timeline, but commit cards still reveal too little about what actually changed and they do not provide an outbound GitHub commit link. The next slice should enrich commit entries with higher-signal summary detail and a deterministic GitHub URL while keeping `/activity/` as a concise repository-history page rather than a full git browser.

## User Stories
- As a developer, I want each commit entry on `/activity/` to show more detail about what happened so that I can understand the change without leaving the timeline immediately.
- As a user, I want a link from the commit entry to the corresponding GitHub commit page so that I can open the hosted view when it exists.
- As an operator, I want the GitHub link generation to be deterministic even if the remote page does not exist yet, so the UI stays predictable across environments.
- As a maintainer, I want the extra commit detail to stay concise and curated so that `/activity/` remains a readable repository-history surface rather than turning into an in-app diff browser.

## Core Requirements
- The slice must enrich commit entries on `/activity/` with more detail about what changed in the commit.
- The slice must include the touched file list for commit entries, with explicit visibility for any updated `.md` files.
- The slice must include concise commit metadata on each card: subject, short hash, author, timestamp, and activity or change type.
- The slice must include a compact summary of what areas changed, such as total touched-file count and counts or highlights for canonical content, moderation, docs, and other code or config paths.
- The slice must surface canonical post or moderation targets when those can be derived from touched paths.
- The slice must add a GitHub commit link for commit entries, and the link may be shown even when the remote page does not yet exist.
- The slice must use a deterministic source for GitHub URL generation so the same commit always maps to the same outbound URL shape.
- The slice must keep commit detail concise and high-signal rather than embedding full diffs, patch views, or free-form git exploration tools.
- The slice must preserve the existing filtered timeline model for content, moderation, and code activity rather than splitting commit details onto a separate route.

## Shared Component Inventory
- Existing canonical route: extend `/activity/` in `forum_web/web.py` rather than introducing a commit-detail page.
- Existing git commit read model: extend `GitCommitEntry` and the current git-log helper path so each activity commit carries the extra metadata needed for touched-file lists, `.md` highlights, area counts, canonical targets, and outbound links.
- Existing commit-card rendering: adapt the current commit-card rendering in `forum_web/web.py` so additional commit facts, touched-file summaries, canonical targets, and the GitHub link appear inside the existing card layout.
- Existing activity template shell: keep using `templates/activity.html` as the page shell, with any layout changes limited to the existing card stack.
- Existing repository configuration surface: reuse or define one deterministic repo-origin setting that can be used to build GitHub commit URLs from commit ids.
- Existing filter/navigation behavior: preserve the current `all`, `content`, `moderation`, and `code` filtering model without introducing extra query complexity.

## Simple User Flow
1. A reader opens `/activity/` and sees the normal filtered repository-history timeline.
2. The reader opens or scans a commit entry and sees a clearer summary of what happened in that commit, including the subject, short hash, author, timestamp, activity type, touched files, explicit `.md` updates, and any relevant canonical targets.
3. The same commit entry includes a GitHub link derived from the configured repository origin and the commit id.
4. The reader follows the GitHub link when they want the hosted commit view, or stays on `/activity/` when the enriched card already provides enough context.

## Success Criteria
- Commit entries on `/activity/` show materially more information about what changed than the current minimal card view, including touched files and explicit `.md` updates.
- Commit entries expose concise high-signal metadata including subject, short hash, author, timestamp, change type, area summaries, and canonical targets when available.
- Commit entries expose a deterministic GitHub commit link.
- The page remains readable as a repository-history timeline rather than becoming a diff browser.
- Existing activity filters continue to work with the richer commit presentation.
- The implementation leaves room for outbound links that may not resolve yet without breaking the local activity experience.
