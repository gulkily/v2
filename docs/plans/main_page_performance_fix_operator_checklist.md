## Main Page Performance Fix Operator Checklist

### Goal
- Verify that the main public pages use the intended fast paths after deploy and stay easy to diagnose when they do not.

### Before Traffic
- Confirm the deployed checkout includes the Stage 1-4 changes for request timing headers, cookie-safe native reads, CGI startup behavior, and native profile snapshots.
- Confirm `php_host/public/forum_host_config.php` points `repo_root` at the same checkout that receives content writes.
- Run `./forum env-sync` if the deployed checkout may be missing newer `.env` keys.
- Run `./forum php-host-refresh` from the deployed checkout to rebuild the post index and clear PHP-host caches and static HTML artifacts.

### Warmup
- Request `/` once and confirm the response succeeds.
- Request one existing thread page once and confirm the response succeeds.
- Request one existing profile page once and confirm the response succeeds.
- If you browse with `forum_identity_hint`, repeat those requests with only that cookie present.

### Fast-Path Verification
- Request `/` and confirm the response headers show one of:
  - `X-Forum-Response-Source: php-native-board-index`
  - `X-Forum-Response-Source: php-microcache`
  - `X-Forum-Response-Source: cgi` only when the fast path is still cold or unavailable
- Request `/threads/<existing-thread-id>` and confirm the response headers show one of:
  - `X-Forum-Response-Source: php-native-thread`
  - `X-Forum-Response-Source: static-html`
  - `X-Forum-Response-Source: php-microcache`
- Request `/profiles/<existing-profile-slug>` and confirm the response headers show one of:
  - `X-Forum-Response-Source: php-native-profile`
  - `X-Forum-Response-Source: static-html`
  - `X-Forum-Response-Source: php-microcache`
- Repeat the same checks with only `forum_identity_hint` present and confirm the routes stay on the public fast path.

### Slow-Path Diagnosis
- If a main page responds with `X-Forum-Response-Source: cgi`, inspect:
  - `X-Forum-Request-Duration-Ms`
  - `X-Forum-Cgi-Duration-Ms`
  - `X-Forum-Operation-Id`
- Open `/operations/slow/` and match `X-Forum-Operation-Id` to the recorded request.
- For `/`, `/threads/...`, and `/profiles/...`, confirm the request record now shows named route timings instead of only `No named timing steps recorded`.

### Freshness After Writes
- Submit one normal signed write through the deployed application.
- Request `/`, the affected thread, and the affected profile again.
- Confirm the new content is visible without manual cache clearing.
- Confirm later repeat reads move back onto the expected native/static/public fast path.

### Fallback Boundaries
- Request `/threads/<id>?format=rss` or another query-bearing route variant and confirm it does not pretend to be a native public read.
- Request a profile update or merge route and confirm it stays on the existing dynamic path.
- If possible, send an unexpected cookie and confirm the request falls back safely instead of using a public native response.

### Expected Outcome
- `/`, `/threads/...`, and `/profiles/...` should stop appearing as common slow Python requests during normal browsing.
- `/activity/` may still remain one of the heavier routes; that is expected unless separately optimized.
