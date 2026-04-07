# Compose Reply Latency Reduction Step 3: Development Plan

## Stage 1
- Goal: Make `/compose/reply` latency diagnosable by recording named timing steps around route selection, repository reads, and reply-target rendering.
- Dependencies: Approved Step 2; existing slow-operation and request timing surfaces.
- Expected changes: Add lightweight timing capture to the Python `/compose/reply` read path so production and tests can distinguish CGI startup, post-index readiness, targeted data loading, and render work; extend route-facing tests or operation-event coverage where practical.
- Verification approach: Run focused request/operation-event tests and confirm slow `/compose/reply` reads no longer appear without meaningful timing breakdowns.
- Risks or open questions:
  - Timing must stay cheap enough that it does not become part of the latency problem.
- Canonical components/API contracts touched: `/compose/reply`, request dispatch in `forum_web/web.py`, `record_current_operation_step(...)`, slow-operation visibility.

## Stage 2
- Goal: Simplify the Python `/compose/reply` implementation so it loads only the thread, parent-post, moderation, and author context required for reply compose.
- Dependencies: Stage 1; existing compose reply behavior in `forum_web/web.py`.
- Expected changes: Replace broad `load_repository_state()` usage in the reply-compose path with smaller targeted helpers and a narrower route contract; planned contracts such as `load_compose_reply_context(thread_id: str, parent_id: str | None) -> ComposeReplyContext` or equivalent lookup helpers; preserve current locked-thread, hidden-post, and missing-resource behavior.
- Verification approach: Run focused compose-reply tests plus any targeted route tests for hidden parent posts, locked threads, and default-parent fallback.
- Risks or open questions:
  - Reply reference rendering may still require a narrow slice of identity resolution that must stay explicit.
  - The simplified path must not silently drift from thread/post visibility rules used elsewhere.
- Canonical components/API contracts touched: Python `/compose/reply` route, `render_compose_reference(...)`, moderation visibility helpers, compose reply tests.

## Stage 3
- Goal: Define and build the canonical PHP-ready reply-compose read contract independent of Python rendering internals.
- Dependencies: Stage 2; existing PHP-native read artifact patterns.
- Expected changes: Introduce a shared artifact or snapshot builder for reply-compose context that contains only the data needed to render the page and reply target; planned contracts such as `build_compose_reply_snapshot(...) -> dict[str, object]`, `refresh_compose_reply_snapshot(...) -> None`, or equivalent read-model helpers; keep the compose HTML shell and browser-signing assets as shared canonical surfaces.
- Verification approach: Run focused snapshot/contract tests that validate visible parent-post data, locked-thread state, missing-resource behavior, and parity of key render inputs.
- Risks or open questions:
  - Snapshot invalidation must stay bounded so reply-compose artifacts do not thrash on unrelated writes.
  - The contract must be small enough to mirror in PHP without recreating Python-only identity machinery.
- Canonical components/API contracts touched: reply-compose read contract, PHP-native artifact builder strategy, `templates/compose.html`, canonical reply-reference inputs.

## Stage 4
- Goal: Add a full PHP-native `/compose/reply` route that serves ordinary reply-compose reads without requiring Python execution.
- Dependencies: Stage 3; existing PHP host native-read routing model.
- Expected changes: Extend `php_host/public/index.php` and related helpers to recognize eligible `/compose/reply` requests, load the shared reply-compose artifact, and render the existing compose page shell plus reply-reference content in PHP; preserve explicit fallback to Python when the artifact is missing or the request is outside the supported contract.
- Verification approach: Run focused PHP host tests covering native hit, artifact-missing fallback, missing thread/post, hidden parent post, and locked-thread cases.
- Risks or open questions:
  - Query-parameterized routes need careful eligibility rules so only the supported `thread_id` and `parent_id` shape uses the PHP-native path.
  - PHP rendering must stay structurally aligned with the canonical compose template rather than forking markup.
- Canonical components/API contracts touched: `php_host/public/index.php`, `php_host/public/cache.php` route gating, shared reply-compose artifact loader, canonical compose shell contract.

## Stage 5
- Goal: Lock in Python/PHP parity and production verification for the final `/compose/reply` fast path.
- Dependencies: Stages 1-4.
- Expected changes: Add parity-style tests for the rendered reply-compose page and operator-visible response-source verification; document how to confirm whether `/compose/reply` is using PHP-native rendering or a Python fallback in production.
- Verification approach: Run focused parity and PHP host tests, then exercise a representative `/compose/reply?thread_id=...&parent_id=...` request and confirm the expected response-source/timing headers.
- Risks or open questions:
  - Exact full-page HTML parity may be too brittle and may need to focus on key semantic markers instead.
- Canonical components/API contracts touched: compose reply page tests, PHP host response headers, operator verification docs under `docs/`.
