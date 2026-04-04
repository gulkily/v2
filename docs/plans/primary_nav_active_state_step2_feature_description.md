# Primary Nav Active State Step 2: Feature Description

## Problem
The shared primary nav does not currently show which top-level page or section the user is viewing. This makes navigation weaker across the site, especially when the user is inside `/activity/` and its filtered subsections still conceptually belong to the same `Activity` section.

## User stories
- As a reader, I want the shared navbar to show my current page so that I can orient myself quickly.
- As a reader browsing activity filters, I want `Activity` to remain visibly selected across all activity subsections so that I understand I am still inside the same section.
- As an operator using either the Python or PHP-served read path, I want the navbar state to behave consistently so that the interface does not feel split by runtime.

## Core requirements
- The shared primary nav must visibly indicate the active top-level section for supported page views.
- All `/activity/` views, including filtered subsections such as `all`, `content`, `moderation`, and `code`, must keep `Activity` selected in the shared nav.
- The active state must be correct in the initial rendered HTML rather than depending on later client-side enhancement.
- The behavior must remain consistent across the Python-rendered shell and the PHP-hosted read path.
- The feature must reuse the existing shared header/navigation surface rather than introducing a second navigation pattern.

## Shared component inventory
- [`forum_web/templates.py`](/home/wsl/v2/forum_web/templates.py)
  Reuse and extend the canonical shared header/nav render path because it already owns the primary nav for Python-rendered pages.
- [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php)
  Reuse and extend the PHP shared shell so the same active-section behavior appears on the PHP-hosted read path.
- [`templates/page_shell_content.json`](/home/wsl/v2/templates/page_shell_content.json)
  Reuse the existing shared nav content source; this feature should extend the existing shared-shell contract rather than fork link definitions.
- [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py)
  Extend the canonical route render paths because they already know which top-level section each page belongs to.
- [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py): `render_activity_filter_nav`
  Reuse as the page-local activity subsection selector; it should remain distinct from the top-level primary nav state.
- [`templates/assets/site.css`](/home/wsl/v2/templates/assets/site.css)
  Extend the existing shared nav styling rather than introducing a separate component or one-off page-specific styling.

## Simple user flow
1. The user opens a top-level page such as home, compose, instance, or activity.
2. The shared page shell renders the primary nav with the matching section visibly selected.
3. If the user enters `/activity/` with a subsection filter such as `view=moderation` or `view=code`, the page-local filter still shows the selected stream.
4. The shared primary nav continues to show `Activity` as the active top-level section throughout those subsection changes.

## Success criteria
- Users can identify the active top-level section from the shared navbar on supported pages without relying on page body context alone.
- `/activity/`, `/activity/?view=all`, `/activity/?view=content`, `/activity/?view=moderation`, and `/activity/?view=code` all render with `Activity` selected in the primary nav.
- The active-nav behavior is consistent between the Python-rendered shell and the PHP-hosted read path.
- No second navigation pattern is introduced for solving this selection-state problem.
