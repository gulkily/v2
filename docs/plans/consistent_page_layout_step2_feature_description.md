## Problem
The web app already has a shared base page template, but it currently presents at least two distinct layout patterns: the default site shell and the front-page variant used by the board index and activity pages. The next slice should make page layout feel consistent across the full web experience by converging on one canonical shell and aligning existing pages to it without expanding into a full visual redesign or unrelated feature work.

## User Stories
- As a reader, I want every page to feel like part of the same site so that navigation and page structure stay predictable.
- As a reader, I want the homepage, activity page, thread pages, and planning pages to share the same basic shell so that moving between them does not feel jarring.
- As a maintainer, I want one canonical layout path so that future pages reuse the same header, footer, navigation, and width rules instead of introducing new page shells.
- As a future implementer, I want layout consistency to be solved through existing shared rendering surfaces so that follow-on page work does not fork the UI structure again.

## Core Requirements
- The slice must define one canonical page layout structure for the web UI, including shared header, footer, navigation, and main content framing.
- The slice must apply that shared structure across the existing primary page set rather than leaving the current front-page variant as a separate long-term layout track.
- The slice must preserve each page's core content purpose while making the surrounding shell consistent.
- The slice must keep the work scoped to layout consistency and avoid a broader typography, branding, component-library, or information-architecture rewrite.
- The slice must leave future pages with a clear default shared layout path so new routes do not recreate the current inconsistency.

## Shared Component Inventory
- Existing canonical page renderer: reuse and extend `forum_web/templates.py:render_page` as the primary shared page-shell contract because it already owns the base template and default header/footer behavior.
- Existing base layout template: reuse `templates/base.html` as the single outer document shell rather than introducing a second top-level page frame.
- Existing default site shell: treat the current default header, footer, navigation, and content-shell behavior from `render_page` as the baseline canonical layout to reuse or extend.
- Existing front-page layout path: refit the board index and activity pages, which currently use `page-shell-front` and custom front-header/front-footer treatment, into the canonical shared shell rather than preserving them as a separate long-term layout system.
- Existing page templates: extend the current route templates such as board index, activity, thread, compose, profile, instance, moderation, task detail, and task priorities so they fit inside the unified shell instead of creating new page-specific layout wrappers.
- New UI surfaces: none required unless a small shared partial or helper is needed to keep the canonical shell reusable; if added, it should support the shared shell rather than create another layout branch.

## Simple User Flow
1. A reader opens any primary route in the web UI.
2. The page presents the same overall header, navigation, footer, and content framing as other pages.
3. The reader moves to a different route such as the homepage, activity view, a thread page, or a planning page.
4. The destination page keeps its own content but preserves the same surrounding layout structure.
5. The reader can navigate the site without encountering a visibly separate layout system.

## Success Criteria
- The homepage, activity page, and the main interior pages share one recognizable layout shell.
- Primary navigation, footer treatment, and page-width/content framing are consistent across the existing web routes.
- No primary page depends on a separate long-term layout system that duplicates the canonical shell.
- Each page still preserves its core content and task focus after the layout unification.
- Future page work has one clear shared layout path instead of multiple competing shell patterns.
