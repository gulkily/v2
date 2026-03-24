1. Stage 1: Define the static-public-read contract
   Goal: establish the allowlisted route set, artifact location contract, and helper boundaries for direct static serving in PHP-shim mode.
   Dependencies: Approved Step 2; existing PHP host entry rules in [`php_host/public/.htaccess`](/home/wsl/v2/php_host/public/.htaccess), [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php), and [`php_host/public/cache.php`](/home/wsl/v2/php_host/public/cache.php).
   Expected changes: add or extend conceptual helpers such as `forum_static_html_request(): bool`, `forum_static_html_public_path(string $requestPath, string $queryString = ""): ?string`, and config support for a public artifact root; no database changes.
   Verification: manual request-shape checks plus focused PHP tests proving only allowlisted anonymous reads qualify and request-sensitive routes still fall through dynamically.
   Risks/Open questions: artifact path must be public-web-root-safe; query normalization must not create alias collisions.
   Canonical components/contracts touched: Apache rewrite contract, PHP host config contract, existing public-read allowlist policy.

2. Stage 2: Add web-server bypass and dynamic fallback
   Goal: let Apache serve valid generated HTML files directly before invoking the PHP front controller.
   Dependencies: Stage 1 contract and artifact-path mapping.
   Expected changes: extend [`php_host/public/.htaccess`](/home/wsl/v2/php_host/public/.htaccess) rewrite behavior for allowlisted route-to-artifact lookups; keep [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php) as fallback for misses, dynamic routes, and writes; no database changes.
   Verification: manual smoke checks for static hit, static miss, asset request, write route, and cookie-bearing request; PHP-host integration coverage where practical.
   Risks/Open questions: Apache rewrite portability on shared hosts; avoiding accidental direct serving of stale or partial files.
   Canonical components/contracts touched: public web root entry rules, front-controller fallback semantics, existing asset-serving behavior.

3. Stage 3: Generate and invalidate canonical public HTML artifacts
   Goal: make the Python read surface produce and refresh the direct-serve HTML artifacts for allowlisted public pages.
   Dependencies: Stages 1-2; canonical rendering in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py).
   Expected changes: add conceptual helpers such as `render_static_html_artifact(path: str, query_string: str = "") -> bytes | None`, `store_static_html_artifact(path: str, body: bytes) -> None`, and `invalidate_static_html_artifacts(reason: str, affected_paths: Iterable[str] | None = None) -> None`; keep canonical page rendering in Python; no database changes.
   Verification: targeted tests around artifact generation for allowlisted reads and invalidation after relevant content/profile/moderation writes, plus manual freshness checks.
   Risks/Open questions: mapping a write to all affected read paths; keeping moderation-sensitive or query-variant pages out of the artifact set.
   Canonical components/contracts touched: canonical Python read renderer, write-trigger invalidation boundary, public route-to-artifact mapping.

4. Stage 4: Make the username CTA static-safe before first paint
   Goal: preserve the shared `Choose your username` banner as client-owned UI while removing the visible late reveal on static-served pages.
   Dependencies: existing CTA surfaces in [`forum_web/templates.py`](/home/wsl/v2/forum_web/templates.py), [`templates/assets/username_claim_cta.js`](/home/wsl/v2/templates/assets/username_claim_cta.js), and `/api/get_username_claim_cta` plus `/api/set_identity_hint` in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py).
   Expected changes: add a minimal early client bootstrap contract, likely via shared shell markup and/or head script plus browser-readable account-state storage; keep `/profiles/<identity-slug>/update` as the canonical destination; no database changes.
   Verification: browser-focused tests showing eligible no-username users see the banner before first paint on static and dynamic pages, while unknown or ineligible states stay hidden.
   Risks/Open questions: client state can drift stale; first-paint correctness must not depend on server-only session state.
   Canonical components/contracts touched: shared page shell, CTA asset contract, local account-state storage contract, existing CTA APIs.

5. Stage 5: Tighten docs and end-to-end verification
   Goal: document the deployment/runtime contract and close gaps with integration coverage before implementation signoff.
   Dependencies: Stages 1-4.
   Expected changes: update [`docs/php_primary_host_installation.md`](/home/wsl/v2/docs/php_primary_host_installation.md) and add focused integration/manual verification coverage for direct static hits, fallback misses, invalidation, and first-paint CTA behavior; no database changes.
   Verification: documented smoke checklist for PHP-primary deployments plus automated coverage for the highest-risk routing and freshness cases.
   Risks/Open questions: local tests may not fully simulate shared-host rewrite behavior; manual host validation may still be required.
   Canonical components/contracts touched: deployment instructions, PHP-host verification contract, public-read acceptance criteria.
