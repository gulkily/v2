Problem: The current homepage presents the repository-backed board index in a generic hero-and-card layout that does not match the cleaner, friendlier ZenMemes front-page direction. We need the `/` experience to feel calm, text-first, and welcoming while still exposing the forum's real data and existing destinations.

User stories:
- As a visitor, I want the homepage to feel clean and friendly so that the site is inviting on first load.
- As a reader, I want to scan threads in a compact text-first list so that I can quickly decide what to open.
- As a forum participant, I want the homepage to keep obvious paths to posting and other key areas so that the redesign improves orientation instead of hiding capabilities.
- As a mobile user, I want the layout to stay readable and navigable on small screens so that the new design works beyond desktop.

Core requirements:
- Replace the current `/` board index presentation with a ZenMemes-inspired front-page layout built around header, primary thread list, sidebar, and footer regions.
- Render live repository-backed thread data on the homepage rather than placeholder content, while keeping thread links and key action links intact.
- Preserve existing high-value destinations already surfaced from the board index, including compose thread, instance info, moderation log, and task priorities.
- Keep the homepage accessible and text-first, with visible link states, clear focus order, and a mobile layout that collapses cleanly.
- Treat the ZenMemes mock as a tonal and structural reference only; features not supported by the current product model must not be invented as part of this slice.

Shared component inventory:
- Existing homepage route `/` and board-index renderer: extend as the canonical surface for this feature because the request is to replace the current layout, not add a second homepage.
- Shared page shell in `templates/base.html` and site stylesheet: extend if they can support the homepage without regressing other pages; otherwise add homepage-specific structure/styles while keeping the rest of the app stable.
- Thread detail, post detail, compose, instance info, moderation, and task-priority pages: reuse unchanged as linked destinations from the refreshed homepage.
- Read-only text API surfaces such as `/api/list_index`: reuse unchanged because this feature is visual and should not redefine the data contract.

Simple user flow:
1. User opens `/`.
2. User sees a calm branded header, compact thread list, and supporting sidebar content.
3. User scans thread subjects and metadata, then opens a thread or follows a key action link.
4. User can continue to compose, moderation, instance info, or planning pages without losing orientation.

Success criteria:
- The homepage at `/` presents the new layout instead of the current hero-and-card board index.
- Homepage content is drawn from the existing repository-backed thread data and links correctly into thread pages.
- Existing key destination links from the homepage remain available after the redesign.
- The homepage remains usable on narrow screens and keyboard navigation follows the intended reading order.
- The change stays scoped to homepage presentation and does not require new backend data models or API behavior.
