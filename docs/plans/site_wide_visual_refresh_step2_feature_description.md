Problem: The homepage now has a cleaner front-page style, but the rest of the site still uses the older hero-and-panel presentation, so the product feels visually split. We need the remaining pages to match the new style and remove the homepage's board-tag directory so the site reads as one coherent interface.

User stories:
- As a visitor, I want the whole site to share the new calm visual style so that moving between pages feels intentional instead of jarring.
- As a reader, I want thread, post, and moderation pages to match the homepage language so that the reading experience stays consistent after I click through.
- As a participant, I want compose and profile-related pages to keep their current capabilities while adopting the new style so that the redesign improves clarity without hiding workflows.
- As a developer, I want the redesign to reuse shared rendering patterns so that future UI changes do not require page-by-page visual drift.

Core requirements:
- Restyle the remaining HTML pages to align with the new homepage visual language, including thread, post, moderation, instance info, profile, profile update, compose, task priorities, and task detail surfaces.
- Remove the homepage "Browse by board tag" section while preserving the homepage's core thread stream and key destination links.
- Reuse or extend the shared page shell and existing templates so the redesign stays coherent across the site.
- Preserve current routes, page purposes, and backend behavior; this feature changes presentation, not forum capabilities or API contracts.
- Keep the refreshed pages accessible and readable on narrow screens, with visible links, predictable focus order, and stable content hierarchy.

Shared component inventory:
- Shared page renderer and base shell in `forum_web/templates.py` and `templates/base.html`: extend as the canonical site-wide frame because multiple pages already depend on this shared contract.
- Shared stylesheet in `templates/assets/site.css`: extend as the canonical styling surface because the redesign should converge on one visual language instead of parallel page-specific themes.
- Homepage template `templates/board_index.html`: extend to remove the board-tag directory while preserving the front-page stream and key links.
- Read surfaces `templates/thread.html`, `templates/post.html`, `templates/moderation.html`, `templates/instance_info.html`, `templates/profile.html`, `templates/task_detail.html`, and `templates/task_priorities.html`: reuse as the canonical page templates and restyle them rather than replacing routes or splitting them into alternate versions.
- Write-oriented surfaces `templates/compose.html` and `templates/profile_update.html`: reuse as the canonical interaction templates and restyle them without changing their underlying command or browser-signing behavior.
- Read-only API surfaces such as `/api/list_index`: reuse unchanged because this feature is limited to the HTML UI.

Simple user flow:
1. User opens `/` and sees the simplified homepage without the board-tag directory.
2. User opens a thread, post, profile, compose, or planning page.
3. Each destination keeps its current content and purpose but presents it in the same visual language as the homepage.
4. User can continue moving through the site without hitting an older-looking layout mode.

Success criteria:
- The remaining HTML pages visibly match the homepage's calm text-first style instead of the older hero-based presentation.
- The homepage no longer shows the "Browse by board tag" section.
- Existing page routes and core actions still work without backend or API changes.
- The redesign preserves readability and navigation on both desktop and narrow screens.
- The result feels visually consistent across homepage, read pages, compose flows, and planning surfaces.
