Problem: The current UI still includes repeated explanatory copy, low-value section labels, and affordances that suggest functionality the product does not actually provide yet, which makes the interface feel heavier and less trustworthy than it should. We need to simplify the site by removing or hiding non-essential text and unfinished affordances while keeping the core workflows understandable.

User stories:
- As a reader, I want pages to show only the text I need so that the interface feels calmer and easier to scan.
- As a participant, I want important actions to remain visible without being surrounded by repeated explanations so that I can complete workflows faster.
- As a user, I want unfinished or non-functional affordances hidden so that the site does not suggest capabilities that do not work.
- As a designer/developer, I want simplification applied consistently across templates so that the site feels intentionally minimal instead of unevenly trimmed.

Core requirements:
- Remove or reduce duplicated, low-value, or overly explanatory text across the existing HTML templates while preserving the minimum guidance required for key flows.
- Hide affordances that imply incomplete functionality, including homepage tag links that do not lead to real destinations.
- Keep primary actions and essential navigation visible on homepage, thread, compose, profile, moderation, and planning surfaces.
- Preserve current routes, form hooks, table hooks, and backend behavior; this is a presentation simplification pass, not a feature change.
- Keep the simplified UI readable and understandable without forcing users to guess what a page or action does.

Shared component inventory:
- Shared page templates and renderer in `forum_web/templates.py`, `forum_web/web.py`, and `templates/*.html`: extend as the canonical simplification surface because the duplicated text and affordances live in those existing templates and render helpers.
- Homepage header/action affordances in `render_board_index_header(...)` and `templates/board_index.html`: extend to remove or hide tag-link affordances that currently do not act like real navigation.
- Shared item-block rendering in `render_post_card(...)` and related helpers: reuse and simplify where repeated labels or low-value metadata still appear.
- Compose and profile-update templates: reuse as the canonical write-surface templates, but trim explanatory copy without changing browser-signing DOM hooks.
- Planning/profile/detail templates: reuse as the canonical read/planning surfaces, but remove repeated headings and copy where the page structure already communicates the same information.
- Read-only API surfaces such as `/api/list_index`: reuse unchanged because this feature is limited to HTML UI copy and affordances.

Simple user flow:
1. User opens the homepage and sees only working, meaningful actions instead of decorative or unfinished navigation.
2. User opens a thread, compose page, profile, or planning page and encounters less repeated explanation and fewer low-value labels.
3. User still finds the primary action or information they need without losing essential context.
4. User moves through the site with less visual and cognitive clutter.

Success criteria:
- Non-functional or misleading affordances such as homepage tag links are hidden or removed.
- Repeated or low-value explanatory text is reduced across representative homepage, read, write, and planning pages.
- Core actions, routes, and workflow hooks remain intact after simplification.
- The resulting pages are easier to scan while still leaving enough context for users to understand what to do next.
- The cleanup feels consistent across the site rather than limited to one template.
