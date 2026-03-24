## Problem
The PHP-primary host profile still routes safe public reads through the PHP shim even when the response could be served as a pre-generated HTML file. The next slice should let allowlisted anonymous read pages bypass PHP entirely when a valid static artifact exists, while keeping request-sensitive behavior in client-side code or on dynamic routes so public pages stay fast without losing essential UX.

## User Stories
- As an anonymous visitor, I want board, thread, post, profile, and other safe public pages to load from static HTML when possible so linked traffic does not depend on PHP or Python rendering for every hit.
- As a deployer on a PHP-primary host, I want the optimization to live in the existing host entry layer so that the canonical Python app remains the source of truth for route semantics and rendered content.
- As a signed-in or returning browser user without a username, I want the shared `Choose your username` banner to appear immediately on eligible pages so static serving does not make account setup guidance feel delayed or broken.
- As a maintainer, I want the static-serving boundary to stay explicit so request-sensitive, personalized, or mutation-related routes do not accidentally become frozen shared HTML.

## Core Requirements
- In PHP-shim mode, the host must serve pre-generated HTML directly for an explicit allowlist of anonymous public read routes when a valid artifact exists, without routing those requests through the PHP front controller.
- The canonical Python application must remain the source of truth for generating public HTML artifacts, route output, and invalidation decisions; the feature must not introduce a second renderer or duplicate page definitions.
- Routes whose output depends on cookies, sessions, request headers, query variants, permissions, moderation-only state, or per-request tokens must remain dynamic and must not be served from shared static HTML.
- The shared `Choose your username` banner must remain client-owned and must render in its correct visible or hidden state before first paint on static-served pages when the browser already has enough local account state to decide.
- The slice must keep existing write flows, compose flows, signed submission APIs, and canonical profile-update behavior unchanged apart from any invalidation needed to keep public static HTML fresh after relevant writes.

## Shared Component Inventory
- Existing PHP host entry rules in [`php_host/public/.htaccess`](/home/wsl/v2/php_host/public/.htaccess): extend as the canonical static-bypass gate because Apache already decides whether to serve a real file or route through [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php).
- Existing PHP front controller in [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php): reuse as the dynamic fallback for non-allowlisted routes, cache misses, writes, and host setup failures rather than creating a second dynamic entry path.
- Existing canonical read renderer in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py) and shared shell rendering in [`forum_web/templates.py`](/home/wsl/v2/forum_web/templates.py): reuse as the only source for public page HTML and shared banner markup.
- Existing username CTA asset in [`templates/assets/username_claim_cta.js`](/home/wsl/v2/templates/assets/username_claim_cta.js): extend its client-side ownership so the banner can decide visibility from browser-available state without depending on server-rendered personalization on static pages.
- Existing CTA and identity APIs at `/api/get_username_claim_cta` and `/api/set_identity_hint` in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py): reuse for eligibility refresh and client-state synchronization; no new username-claim flow is introduced.
- Existing profile-update route `/profiles/<identity-slug>/update`: reuse as the canonical destination for eligible no-username users; this feature improves delivery and first-paint behavior, not account-flow structure.

## Simple User Flow
1. An anonymous visitor requests an allowlisted public read route on a PHP-primary deployment.
2. If a valid pre-generated HTML artifact exists for that route, Apache serves it directly; otherwise the request falls through to the existing PHP front controller and canonical app path.
3. The returned page includes the shared client-owned username CTA shell and early client state needed to decide whether the banner applies on this browser.
4. If the browser has local state showing an eligible no-username user, the banner appears immediately and links to the existing profile-update flow; otherwise it stays hidden.
5. After relevant content or profile changes, later requests receive regenerated public HTML rather than stale artifacts.

## Success Criteria
- Allowlisted anonymous public read routes can be served directly from pre-generated HTML on PHP-primary deployments without invoking the PHP front controller on cache hits.
- Non-allowlisted, request-sensitive, and mutation-related routes continue to use the existing dynamic path and do not expose frozen personalized or write-state UI.
- Static-served pages and dynamically served pages present the same canonical public content for the same route once artifacts are fresh.
- Eligible no-username users see the shared `Choose your username` banner in the correct state before first paint on static-served pages, while ineligible or unknown-state browsers do not see a misleading prompt.
- The feature stays narrow: it improves public-read delivery and static-safe first-paint UX without introducing a new renderer, a new username-claim workflow, or broader session-based personalization.
