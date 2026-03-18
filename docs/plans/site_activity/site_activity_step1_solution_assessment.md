# Site Activity Step 1: Solution Assessment

## Problem statement
The homepage has only one “view moderation log” action, yet the TODO describes a desire for a git-linked site activity page/feed; we need to tip that entry toward a broader “site activity + git info” surface so users can see new content and the repo’s commit state without drifting into the moderation log alone.

## Option A — Build a `/activity/` landing page that merges the latest canonical posts/replies with repo metadata
- Pros: Matches the TODO’s “newest content feed together with git log”; keeps the moderation log as a narrower “filters” page; anaemic to extension (just need to render recent records and `git log`/`git status` output). Simplifies the front-page action to one site-activity link.
- Cons: Requires a new template, a controller that reads canonical records and shelling out for git information, plus styling for the mix of posts and metadata.

## Option B — Repurpose the existing moderation log view into the site activity feed
- Pros: Reuses the established `/moderation/` route, template, and data access; minimal routing changes (just inject git info and relabel the action link).
- Cons: Moderation log is already focused on policy events; adding a general feed and git details may dilute its narrative and confuse the button label; moderation log filters might mention things we don’t intend for the general audience.

## Recommendation
Start with Option A: introduce a dedicated `/activity/` page that renders recent post records and repo metadata (commit ID/date, instance status, etc.), and make the front-page action link point there instead of `/moderation/`. The existing moderation log can stay as a secondary tool while `/activity/` delivers the “new content + git info” promise the TODO captures.
