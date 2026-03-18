## Problem
`/activity/` currently combines git-backed content commits and moderation records, but it still excludes other repository commits such as code changes, which leaves the page short of the broader repository-history role now desired. The next slice should expand `/activity/` into a broader all-commits repository event browser with fixed filters for content, moderation, and code activity, without drifting into a full general-purpose git UI.

## User Stories
- As a developer, I want code-modification commits to appear in `/activity/` so that engineering changes are visible alongside other repository events.
- As an operator, I want fixed filters for content, moderation, and code activity so that I can narrow the timeline to the event class I care about.
- As a reader, I want one canonical reverse-chronological timeline for repository history so that I can understand what changed on the instance without visiting multiple pages.
- As a maintainer, I want commit classes to remain explicit and fixed so that `/activity/` becomes a broader repository-history surface without becoming a full git browser.

## Core Requirements
- The slice must extend `/activity/` to include repository commits beyond canonical post-content commits, including code-modification commits.
- The slice must preserve one combined reverse-chronological timeline in the default view and add a fixed code-activity filter alongside the existing filter modes.
- The slice must define a deterministic commit-classification rule so commits can be surfaced as content, moderation, code, or another explicit repository-history class as needed.
- The slice must keep the page scoped to curated repository history, not arbitrary git browsing features such as commit diffs, branch navigation, or free-form query tooling.
- The slice must preserve clear navigation from activity items into the most relevant existing context when such a context exists, while still rendering code-only commits intelligibly when no canonical post target exists.

## Shared Component Inventory
- Existing canonical activity route: extend `/activity/` in `forum_web/web.py` as the broader repository-history page rather than introducing a second code-history route.
- Existing git commit read model: extend `fetch_recent_commits(...)` and the current git-log-backed activity helper path so it can classify and expose commits beyond `records/posts` changes.
- Existing merged activity model: extend `ActivityEvent`, `activity_filter_mode_from_request(...)`, and `load_activity_events(...)` instead of creating a separate event system parallel to the current merged timeline.
- Existing moderation read model: preserve `load_moderation_records(...)` and moderation-event rendering as one explicit class inside the broader repository timeline.
- Existing activity page template: extend `templates/activity.html` and the current mixed event-card rendering so code commits can appear alongside content and moderation activity in one page shell.
- Existing commit-card rendering: reuse or adapt the current commit-card path for code commits, adding only the minimal extra metadata needed to distinguish code-focused entries from content-focused entries.

## Simple User Flow
1. A reader opens `/activity/` and sees a default reverse-chronological repository-history timeline that can include content commits, moderation events, and code commits.
2. The reader uses fixed filters to switch among all activity, content activity, moderation activity, and code activity.
3. The page updates to show only the selected class while keeping the same overall layout and ordering model.
4. When an item maps to an existing thread, post, or moderation context, the reader can follow that link; code-only commits still remain understandable as repository events even without canonical post targets.

## Success Criteria
- `/activity/` includes code-modification commits in addition to content and moderation activity.
- The page exposes a fixed code-activity filter alongside the existing activity filters.
- The default `all activity` view remains one reverse-chronological timeline across the included repository event classes.
- Commit/event classification is deterministic enough that content, moderation, and code filters return the expected subsets.
- `/activity/` becomes the broader repository-history surface without adding generic git-browser features outside the curated activity scope.
