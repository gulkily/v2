## Stage 1
- Goal: add the minimal PHP-front-controller cache policy for safe public reads and static asset headers.
- Dependencies: approved Step 2; current PHP shim in [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php); existing canonical read route contract in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py).
- Expected changes: extend the PHP adapter with small request-shape helpers, an explicit allowlist for cacheable `GET` routes, a short-lived file-backed microcache read/write path, and asset-response cache headers for canonical `/assets/...` routes; planned PHP helper contracts such as `forum_cacheable_read_request(): bool`, `forum_cache_dir(): string`, `forum_read_cached_response(): ?string`, `forum_store_cached_response(string $response): void`, and `forum_asset_cache_headers(): array`; no database changes.
- Verification approach: manually request `/`, one thread page, one post page, one allowed read API route, and one asset route through `php php_host/public/index.php`; confirm cacheable reads return canonical bodies and assets emit cache headers.
- Risks or open questions:
  - keeping the allowlist narrow enough that compose flows, write paths, and request-context-sensitive routes remain uncached
  - choosing a writable default cache directory that works on typical shared hosts without widening scope
- Canonical components/API contracts touched: PHP front controller only; canonical Python read rendering stays unchanged.

## Stage 2
- Goal: ensure successful writes invalidate the PHP microcache and add focused PHP-shim coverage around the cache behavior.
- Dependencies: Stage 1; existing canonical write endpoints `/api/create_thread` and `/api/create_reply`; current PHP CLI smoke harness pattern.
- Expected changes: add adapter-side invalidation that clears cached public reads after successful mutating requests routed through the PHP shim, keep write responses themselves uncached, and add a targeted end-to-end test or harness that exercises cache miss, cache hit, asset headers, and invalidation after a successful write; planned helper contracts such as `forum_mutating_request(): bool` and `forum_clear_cache(): void`; no database changes.
- Verification approach: run the targeted cache smoke/test flow with a temporary repo and cache directory, confirm the second identical read is served from cache, then submit a canonical write and confirm the next read is regenerated from fresh Python output.
- Risks or open questions:
  - deciding whether invalidation should clear the full cache directory or only known route keys in this first slice
  - keeping the verification seam stable without introducing a dedicated PHP test framework
- Canonical components/API contracts touched: `/api/create_thread`; `/api/create_reply`; PHP shim request-forwarding contract; canonical repository write behavior remains unchanged.

## Stage 3
- Goal: document the host-side cache behavior and lock the feature into final manual verification guidance.
- Dependencies: Stages 1-2; current operator guidance in [`docs/php_primary_host_installation.md`](/home/wsl/v2/docs/php_primary_host_installation.md).
- Expected changes: extend the PHP-primary host installation doc with the writable cache directory expectation, any adapter env knobs for cache location or TTL, the allowlisted-scope boundary, and post-install checks for read caching and write invalidation; update the Step 4 implementation summary during execution, but no new runtime surfaces or database changes.
- Verification approach: repeat the PHP-host smoke pass described in the docs, including one cached read, one asset request, and one write followed by a fresh read; confirm the documentation matches the implemented adapter behavior exactly.
- Risks or open questions:
  - documenting enough operator detail to be actionable without implying support for broader cache customization
  - keeping the stated staleness window explicit and short so deployers understand the tradeoff
- Canonical components/API contracts touched: PHP-primary install guide; existing public route and write-endpoint contracts only.
