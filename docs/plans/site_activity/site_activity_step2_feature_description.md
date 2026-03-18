# Site Activity Step 2: Feature Description

## Problem
The home page currently exposes only the “view moderation log” action, yet the TODO asks for a git-backed activity feed so visitors can understand the most recent forum records alongside repo metadata; we need a clearer entry point that delivers both live content and git information without further cluttering the moderation experience.

## User stories
- As a reader, I want an “activity” landing page so I can see the freshest canonical posts/replies plus the repo commit state in one glance instead of hunting through logs.
- As a reviewer, I want the homepage action in that nav bar to drop me directly into the combined activity view so I can read recent content while confirming the source commit ID/date.
- As a moderator, I want the moderation log to remain its own specialized page (with filters) rather than being the default action on the home page.

## Core requirements
- Add a dedicated `/activity/` endpoint that streams recent thread/post records and displays the current git commit ID/date (and optionally status like `git status` output or repo path) so site state is transparent.
- Replace the home page’s “view moderation log” chip with a “view site activity” or similar link that points to `/activity/`.
- Keep the existing moderation log accessible via `/moderation/` (it can stay linked in secondary navigation or elsewhere) so moderation tooling stays discoverable.
- Reuse existing canonical renderers (thread/post card markup, record-reading helpers) to populate the feed, avoiding new record formats.
- Surface the git metadata in a read-only panel that clearly calls out the git commit fingerprint and timestamp; updates should reflect the repo currently backing the HTTP host.

## Shared component inventory
- `render_board_index_action_links()` / board index header: already renders the navigation chips; we will update it to swap the moderation link for the new activity link.
- `render_post_card()` / thread listing markup: already used to render canonical records; we can reuse this markup to display the feed on `/activity/` so no new UI component is needed.
- `/moderation/` route and template: currently renders moderation log entries; it will remain untouched but now serves as a focused secondary tool rather than the default action on the board index.
- Git instance data (e.g., `render_instance_info_page()`): already surfaces commit/installation details for `/instance/`; we can reuse the existing helpers that fetch `git rev-parse`/`git status` outputs rather than inventing new git plumbing.

## Simple user flow
1. A visitor loads `/` and sees the action navigation chips; the “view moderation log” chip is replaced with “view site activity” or similar.
2. The visitor clicks the activity chip, landing on `/activity/`, which renders a list of recent canonical posts/replies (using the existing thread/post card markup) and a small git metadata panel (commit ID/date, optional status).
3. The visitor can still reach `/moderation/` via a secondary link (e.g., the global footer or a smaller nav element) when they need moderation-specific details.

## Success criteria
- `/activity/` renders without errors and shows the latest canonical content plus the current git commit fingerprint/date pulled from the repo beneath the running instance.
- The home page action chip now links to `/activity/`, while `/moderation/` remains reachable from the site UI.
- No new record formats or storage paths are introduced—existing thread/post card markup and git helpers are reused, keeping the feature surface lightly coupled.
