## Shared Cross-Runtime Read Contract

### Goal
Define one explicit contract for the first PHP-native public read path so Python and PHP implement the same behavior on purpose rather than through copied incidental logic.

### First Covered Route Set
- Covered in v1:
  - `/`
- Explicitly excluded in v1:
  - query-bearing variants such as `/?board_tag=...` or `/?format=rss`
  - thread, post, profile, moderation, compose, and update routes
  - any route with cookies, authorization headers, or non-`GET` methods

### Request Eligibility
- Method must be `GET`.
- Query string must be empty.
- Request must not include cookies or authorization headers.
- The PHP host may attempt the native path only when the request path matches `/`.
- Any request outside that boundary must fall back to the current PHP-to-Python path unchanged.

### Source Of Truth Boundary
- Python remains authoritative for:
  - repository writes
  - post-index refresh and invalidation
  - moderation visibility rules
  - the prepared board-index snapshot consumed by PHP
- PHP is authoritative only for:
  - deciding whether the request matches the native-path eligibility rule
  - rendering the covered route from the prepared snapshot when it is present and valid
  - falling back to Python when the snapshot is missing or invalid

### Prepared Snapshot Contract
- Snapshot scope:
  - one board-index snapshot for `/`
- Snapshot ownership:
  - generated and refreshed by Python
  - read-only from PHP
- Required fields:
  - visible thread rows in final display order
  - per-thread route target, subject, preview text, visible tags, reply count, and thread type label
  - summary counts for posts loaded, visible threads, and board tags
- Excluded fields:
  - per-request personalization
  - write-state controls
  - cookies, CSRF tokens, or request diagnostics

### Render Contract
- PHP-native `/` must preserve these semantics:
  - visible thread ordering matches the Python board index for the same repository state
  - hidden threads do not appear
  - thread links resolve to `/threads/<post-id>`
  - the summary count panel reflects the prepared snapshot values
- PHP-native `/` does not need to reproduce all Python implementation details internally; it only needs to honor the shared snapshot fields and route semantics.

### Fallback Rules
- PHP must fall back to Python when:
  - the snapshot file is missing
  - the snapshot file cannot be parsed
  - the request falls outside the v1 eligibility boundary
- Fallback behavior must preserve the existing PHP-host response path rather than synthesizing partial results.

### Invalidation Boundary
- Any write that can change `/` must invalidate or refresh the board-index snapshot through the Python-owned write path.
- PHP must never attempt to infer invalidation from raw repository changes by itself in v1.

### Expansion Rule
- Additional routes such as `/threads/<id>` or `/profiles/<slug>` may join the native path only after they receive:
  - explicit eligibility rules
  - explicit prepared snapshot fields
  - explicit parity checks against Python behavior
