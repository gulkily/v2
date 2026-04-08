## Problem
Navigation clicks, especially in the shared primary nav, can feel unresponsive because the UI does not visibly react until the destination page begins loading. The next slice should make nav clicks acknowledge immediately while preserving the current server-rendered full-page navigation model.

## User Stories
- As a user, I want the navbar to react instantly when I click a destination so that I know the site received my action.
- As a user on a slower page, I want to see a clear pending state during navigation so that the wait feels intentional instead of broken.
- As a repeat visitor, I want common nav destinations to open faster when possible so that moving around the site feels snappy.
- As a maintainer, I want this improvement to reuse the existing shared header and link-based navigation model so that it works consistently across Python and PHP-served pages.

## Core Requirements
- The shared primary nav must provide immediate visible feedback when a user activates a nav link.
- The feature must preserve normal link navigation, browser history behavior, and full-page loads rather than replacing them with partial-page routing.
- The feature must support both the Python-rendered shared header and the PHP host’s shared header so the behavior is consistent across normal pages.
- Any prefetch behavior must stay narrowly scoped to safe, likely destinations and must not depend on knowing private browser-only identity state in advance.
- The slice must stay focused on perceived navigation responsiveness and must not expand into a broader client-side app shell or site-wide routing redesign.

## Shared Component Inventory
- Existing shared primary nav in [templates.py](/home/wsl/v2/forum_web/templates.py): extend this canonical Python nav surface because it already renders the main header links users click first.
- Existing PHP shared nav renderer in [index.php](/home/wsl/v2/php_host/public/index.php): extend this parallel canonical surface so the same click-response behavior exists on PHP-served pages.
- Existing shared page shell in [templates.py](/home/wsl/v2/forum_web/templates.py): reuse this as the common place to attach any shared nav-enhancement asset on Python-rendered pages.
- Existing browser nav enhancement asset pattern in [profile_nav.js](/home/wsl/v2/templates/assets/profile_nav.js): extend the existing asset approach rather than introducing a new client framework, because the repo already uses lightweight page-level enhancement scripts.
- Existing canonical destination routes such as `/`, `/activity`, `/tasks`, and `/profiles/...`: reuse unchanged because this feature is about navigation response, not new destinations.

## Simple User Flow
1. A user views any page with the shared header.
2. The user clicks a primary nav link.
3. The clicked nav item reacts immediately with a visible pending state.
4. When applicable, the destination may already be warmed by limited prefetch.
5. The browser completes a normal full-page navigation to the selected route.

## Success Criteria
- Clicking a primary nav link produces an immediate visible response on pages that render the shared header.
- Normal browser navigation semantics still work, including full reloads, back/forward history, and direct linking.
- Common safe navbar destinations can be prefetched without changing route ownership or destination content.
- The feature works consistently across both Python-rendered and PHP-hosted pages that use the shared primary nav.
- The slice lands without introducing a partial-page router or other broader app-shell behavior.
