# Site Activity Git Log Step 2: Feature Description

## Problem
`/activity/` currently shows the most recent canonical posts, but the request is to finish the page so it is driven by the git commit log, shows commit fingerprints and dates per item, and orders entries chronologically by the log.

## User stories
- As an editor, I want the activity feed to originate from the git commit log so I can trust that the chronology mirrors the repository history.
- As a reader, I want each activity item to surface the commit fingerprint and commit date so I understand exactly when the referenced change landed.
- As a developer, I want the page to link back to the canonical post and relevant metadata so the git history and HTML view stay synchronized.

## Core requirements
- Query `git log` (or equivalent) for the most recent commits affecting the records directory and render each commit as an activity item, including fingerprint, date, and affected file/record.
- Render items in descending chronological order (newest first) based on git commit timestamps so the log is the definitive ordering principle.
- Each entry should link back to the canonical post/permalink or relevant view built from existing `post-card` markup where possible so visitors can jump from a commit to the record.
- Continue to show repository metadata (commit ID/date, working tree status) in the panel while also surfacing commit-level details in the feed.
- Keep the moderation log/other navigation accessible and consistent with the board index layout; only the activity action chip should point to `/activity/`.

## Shared component inventory
- `templates/activity.html`: new layout for `/activity/`; this feature will reuse the existing hero/footer style but will replace the record loop with a git-driven list.
- `render_post_card()` + `templates/post-card` markup: we can continue reusing this markup when linking to posts from each commit, but we may need a slimmer/compressed variant for commit entries; reusing the component keeps visual consistency.
- `forum_web/repository.py` helpers (`load_posts`, `group_threads`): already parse canonical records; we will continue to read these when resolving the commit’s files to post IDs.
- `forum_core.instance_info.load_instance_info`: supplies commit metadata for the panel; continue calling this helper so the repository snapshot still shows commit info.

## Simple user flow
1. Visitor loads `/activity/`; the activity header/hero renders along with the repository metadata panel.
2. The page executes `git log` (caching the last N commits) and renders each commit as an entry containing the fingerprint, commit date, and a preview/link to the canonical post(s) impacted.
3. Items appear newest-first; selecting a post link takes the user to the existing `/posts/<id>` view for more detail.

## Success criteria
- `/activity/` now renders the most recent git commits (default limit) as chronologically ordered items, each exposing the commit fingerprint/date and linking to the touched record.
- The repository metadata panel continues to show commit ID/date/path and working-tree status, matching the data shown in the git log entries.
- Tests verify that the new commit-driven item list appears, maintains the order, and that the board index action still goes to `/activity/`.
