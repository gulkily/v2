## Stage 1
- Goal: establish the read-only API route shell and deterministic plain-text serialization helpers.
- Dependencies: approved Step 2; existing canonical post reader and web routes.
- Expected changes: add a minimal `/api/` route namespace, define shared read-only serializers for index/thread/post responses, and introduce planned helpers such as `render_index_text(threads) -> str`, `render_thread_text(thread) -> str`, and `render_post_text(post) -> str`; no write endpoints.
- Verification approach: manually request an API route and confirm the response is plain text, stable, and derived from the same repository state as the web renderer.
- Risks or open questions:
  - letting API formatting drift away from later language-neutral fixtures
  - coupling browser and API route handling too tightly
- Canonical components/API contracts touched: canonical post files; initial plain-text read response shapes.

## Stage 2
- Goal: implement the `list_index` read API over the existing sample dataset.
- Dependencies: Stage 1.
- Expected changes: add a read-only index endpoint that lists thread roots in deterministic order and exposes enough plain-text metadata for CLI and agent use; planned helper such as `build_index_rows(threads) -> list[IndexRow]`.
- Verification approach: call the endpoint manually, compare a few entries against the board index page and raw post files, and confirm ordering is deterministic.
- Risks or open questions:
  - balancing concise output against future extensibility
  - deciding whether the first cut is global-only or board-filtered
- Canonical components/API contracts touched: direct-read index behavior; plain-text list response contract.

## Stage 3
- Goal: implement the `get_thread` and `get_post` read APIs using the same repository truth as the renderer.
- Dependencies: Stage 2.
- Expected changes: add plain-text thread and post endpoints, expose deterministic thread ordering and single-post lookup, and reuse the canonical read helpers already proven by the web UI; planned helpers such as `lookup_thread(thread_id) -> Thread | None` and `lookup_post(post_id) -> Post | None`.
- Verification approach: request one known thread and one known post, compare the outputs against the browser views and raw files, and confirm missing resources return a stable plain-text not-found response.
- Risks or open questions:
  - response shape may need later normalization for byte-identical multi-language parity
  - thread output should stay simple enough to align with the protocol draft
- Canonical components/API contracts touched: direct-read thread lookup, direct-read post lookup, plain-text thread and post response contracts.
