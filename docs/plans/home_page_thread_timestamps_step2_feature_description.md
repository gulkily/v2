## Problem
The home page thread listing currently hides thread timing even though the site already derives meaningful post and activity timestamps. Timestamp display is also inconsistent across the site, with some pages showing exact UTC text, some showing commit-formatted dates, and some showing raw timestamp strings instead of one shared friendly presentation.

## User Stories
- As a reader, I want the home page thread listing to show when each thread was last active so that I can quickly judge freshness before opening it.
- As a reader, I want timestamps to read in a friendly form such as `2 hours ago` so that recent activity is easy to scan.
- As a reader, I want the exact timestamp available on hover or inspection so that I can still see the precise time when needed.
- As a maintainer, I want timestamp rendering to extend a canonical shared formatter instead of adding another page-specific date style so that time display stays consistent across the site.

## Core Requirements
- The home page thread listing must display one visible timestamp per thread row that communicates the thread's recency in the same sense used by the current listing order.
- Visible timestamps for this feature must use a friendly relative style such as `2 hours ago` while also exposing the exact timestamp in a `title` or equivalent native tooltip attribute.
- The feature must establish a canonical shared timestamp display surface for server-rendered UI so that home page timestamps reuse the same presentation contract as other timestamped pages.
- Existing timestamped surfaces that already show post, activity, commit, moderation, or operation times should align to the shared display style where that can be done without changing each page's core information architecture.
- The feature must preserve current route shapes, thread links, and existing board index density; timestamps should extend the current listing rather than creating a separate metadata panel or alternate home page layout.

## Shared Component Inventory
- Home page thread rows in `render_board_index_thread_row(...)`: extend this existing canonical listing surface because it is the direct user-visible target of the request.
- Existing post timestamp rendering via `format_post_timestamp(...)` and post-card metadata in `render_post_card(...)`: extend or replace this path with the shared timestamp display contract instead of keeping a second post-only formatter.
- Existing activity and commit date rendering via `format_commit_date(...)` and related activity cards: align these surfaces to the shared timestamp display contract so repository-style time displays do not diverge from post/thread displays.
- Existing surfaces that currently print raw timestamp text such as moderation and operation metadata: migrate these to the shared timestamp display contract where they already expose time to users, rather than preserving ad hoc raw output.
- RSS/feed publication dates and machine-oriented timestamp fields: keep these existing machine-readable contracts unchanged because they serve feed consumers rather than human-facing page rendering.
- PHP/native read board-index snapshot output: extend the canonical home page read model so the public fast path can expose the same timestamp semantics as the Python-rendered home page.

## Simple User Flow
1. A reader opens the home page.
2. Each visible thread row shows a friendly recency label that indicates when the thread was last active.
3. The reader hovers or inspects the timestamp and sees the exact timestamp in the native tooltip/title.
4. When the reader visits other timestamped pages, timestamps follow the same friendly-plus-exact display pattern instead of page-specific formatting styles.

## Success Criteria
- Every visible home page thread row includes a friendly timestamp that reflects the same recency signal used for listing order.
- The exact timestamp remains accessible from the rendered page without requiring a separate detail page.
- Human-facing timestamp displays on the main server-rendered surfaces no longer rely on multiple unrelated formatting styles or raw timestamp strings.
- The home page remains compact and readable after timestamps are added, without displacing thread links, previews, or current navigation behavior.
