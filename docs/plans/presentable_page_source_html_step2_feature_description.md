## Problem
Technical users can inspect page source today, but much of the returned HTML is hard to read because some pages are emitted as long unbroken lines or inconsistent document structures. The next slice should make HTML responses consistently presentable for human inspection across the web app without turning the work into a broader frontend redesign.

## User Stories
- As a technical user, I want browser page source to use readable structure so that I can inspect generated HTML without mentally reformatting it first.
- As a technical user, I want different pages to follow the same presentability conventions so that moving between normal pages, refresh pages, and fallback pages does not feel arbitrary.
- As a maintainer, I want one canonical readable-output standard for HTML responses so that new pages do not regress back to single-line or hard-to-scan markup.
- As a maintainer, I want this work to extend existing rendering surfaces rather than introduce a separate source-only representation that can drift from the actual response.

## Core Requirements
- Normal HTML page responses must become structurally readable by default, including stable line breaks and section boundaries that make browser source inspection practical.
- The feature must apply one shared presentability standard across the app's existing HTML-producing paths rather than improving only one route family.
- The slice must preserve current page behavior and content, changing readability of generated HTML rather than redesigning page visuals or information architecture.
- Existing pages that already render through shared templates should continue to use those canonical rendering surfaces, and direct-response paths should be brought into the same readability standard instead of creating a second long-term pattern.
- The scope must stay focused on HTML source presentability and closely related readability improvements for technical inspection, not on unrelated API, database, or product-flow changes.

## Shared Component Inventory
- Existing canonical page renderer in [`forum_web/templates.py`](/home/wsl/v2/forum_web/templates.py): reuse and extend as the primary shared contract for readable HTML output because it already owns the base document shell and common page assembly.
- Existing base document template in [`templates/base.html`](/home/wsl/v2/templates/base.html): reuse as the canonical outer HTML structure rather than introducing a separate page-source-only shell.
- Existing route templates in [`templates/`](/home/wsl/v2/templates): reuse as the preferred source for readable page structure on template-backed routes; extend only as needed to keep output consistently presentable.
- Existing direct HTML responses in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py): extend these paths so refresh pages, fallback pages, and other non-template responses follow the same readable-output standard instead of remaining a separate single-line branch.
- Existing PHP host fallback pages in [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php): extend these host-rendered HTML pages to match the same presentability standard because they are part of the user-visible web surface even when Python is not serving the response.
- New UI or API surfaces: none required if the feature can be delivered by reusing and extending the existing HTML rendering paths; any new helper should support the canonical response path rather than create an alternate representation.

## Simple User Flow
1. A technical user opens any web page in the app and chooses to inspect its source in the browser.
2. The returned HTML is organized with readable structure instead of collapsing major sections into one long line.
3. The same inspection experience holds across standard application pages, refresh or transition pages, and host-side fallback pages.
4. The user can scan document sections, inline assets, and page content boundaries without needing a separate source-view mode.

## Success Criteria
- Browser-inspected source for the primary HTML page set is readable enough that major document sections are visually separable without manual reformatting.
- Template-backed pages, direct string-built HTML responses, and PHP host fallback pages follow one recognizable presentability standard.
- The feature does not introduce a second source-only rendering mode that can diverge from the actual HTML response.
- Existing page behavior, routing, and user-facing content remain unchanged apart from the improved presentability of the returned HTML.
- Future HTML pages have one clear shared path for staying readable instead of relying on route-by-route formatting choices.
