# Main Page Performance Fix Step 3: Development Plan

## Stage 1
- Goal: Make PHP-native board and thread reads treat `forum_identity_hint` as cache-safe so normal browsing can stay on the intended fast path.
- Dependencies: Approved Step 2; existing cookie-safety helpers in the PHP host.
- Expected changes: Refine native route guards in `php_host/public/index.php` to reuse the existing cache-safety contract from `php_host/public/cache.php`; keep auth headers and unexpected cookies on the CGI fallback path; extend PHP host cache tests for board and thread native reads with identity-hint and unexpected-cookie cases.
- Verification approach: Run focused PHP host tests covering native board/thread reads with no cookie, identity-hint only, and non-allowlisted cookies.
- Risks or open questions:
  - Native route guards and cache helpers may currently encode slightly different safety assumptions that need alignment.
- Canonical components/API contracts touched: `forum_php_native_board_index_route()`, `forum_php_native_thread_route()`, `forum_request_has_cache_busting_credentials()`, PHP host native-read tests.

## Stage 2
- Goal: Stop ordinary CGI reads from paying misleading startup-style post-index work on every request.
- Dependencies: Stage 1; current startup/readiness flow in `forum_web/web.py` and `forum_core/post_index.py`.
- Expected changes: Narrow or remove process-local startup caching assumptions for CGI request handling; ensure the request path only performs read-time index recovery when readiness actually requires it; add or refine tests for repeated CGI-style GET requests so steady-state reads do not trigger avoidable startup maintenance.
- Verification approach: Run focused post-index startup and request-path tests; confirm repeated read requests do not trigger unexpected recovery when the index is current.
- Risks or open questions:
  - Long-lived non-CGI environments may still benefit from process-local readiness shortcuts and may need a separate branch.
  - Production slowness may still include genuine stale-index recovery caused by deploy-state drift.
- Canonical components/API contracts touched: `ensure_runtime_post_index_startup(...)`, request dispatch in `forum_web/web.py`, `ensure_post_index_current(...)`, post-index startup tests.

## Stage 3
- Goal: Make slow main-page requests diagnosable by recording named timing steps for board, thread, and profile reads.
- Dependencies: Stage 2; existing request operation-event model.
- Expected changes: Add lightweight route-specific timing phases to slow `GET /`, `GET /threads/...`, and `/profiles/...` read flows without changing route contracts; extend operation-event-facing tests to assert the new timing visibility where practical.
- Verification approach: Run focused request/operation-event tests and confirm slow-operation rendering no longer shows only `No named timing steps recorded` for these routes in covered scenarios.
- Risks or open questions:
  - Timing additions must stay lightweight and not materially affect the routes they measure.
- Canonical components/API contracts touched: request operation handling in `forum_web/web.py`, `record_current_operation_step(...)`, existing slow-operations rendering/tests.

## Stage 4
- Goal: Add bounded support for a small additional set of hot public PHP-native routes if they still justify expansion after the fast-path fixes.
- Dependencies: Stage 1 complete; production or local re-measurement showing remaining hot public routes outside `/` and `/threads/...`.
- Expected changes: Identify at most a small allowlist of public routes that fit the existing cache-safe/native-read model; extend shared artifact usage and route gating only for those routes; add corresponding eligibility and fallback tests.
- Verification approach: Re-measure route behavior after Stages 1-3; if expansion proceeds, run route-specific PHP host tests and verify the new route stays within the public-read safety model.
- Risks or open questions:
  - This stage should be skipped if Stages 1-3 already remove the practical main-page problem.
  - Additional routes may depend on identity or moderation details that are not safe to mirror in PHP-native form.
- Canonical components/API contracts touched: existing PHP-native artifact readers/builders, PHP host route guards, route-specific tests for any newly allowlisted public route.

## Stage 5
- Goal: Add deploy/warmup verification so the intended fast path stays available in production after releases.
- Dependencies: Stages 1-3; Stage 4 only if additional routes are added.
- Expected changes: Document or script warmup expectations for post-index readiness, board snapshot presence, thread snapshot presence, and representative public-read verification headers; update operator-facing docs/checklists accordingly.
- Verification approach: Run the documented warmup/verification flow locally or in staging and confirm the expected response-source/timing headers match the intended fast paths.
- Risks or open questions:
  - Environment-specific deploy steps may live outside this repo and require a checklist rather than a fully automated command.
- Canonical components/API contracts touched: PHP-native artifacts, post-index readiness expectations, response headers, operator docs under `docs/`.
