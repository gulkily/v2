1. Stage 1: Define the readable HTML output contract
   Goal: establish one canonical presentability standard for HTML responses so readable source does not depend on each route hand-formatting its own markup.
   Dependencies: Approved Step 2; shared page assembly in [`forum_web/templates.py`](/home/wsl/v2/forum_web/templates.py); base document shell in [`templates/base.html`](/home/wsl/v2/templates/base.html).
   Expected changes: conceptually introduce or extend a shared formatting seam for page assembly, such as `render_page(...) -> str` plus a small helper like `format_html_document(html_text: str) -> str` or equivalent shared contract; no database changes.
   Verification approach: manual source inspection on one representative template-backed page to confirm stable line breaks and clear document-section boundaries.
   Risks or open questions: avoid formatting that changes text meaning inside preformatted or script-adjacent content; decide how strict the canonical line-break policy should be without making templates awkward to maintain.
   Canonical components/API contracts touched: `forum_web/templates.py:render_page`; `templates/base.html`; shared HTML document-output contract.

2. Stage 2: Apply the contract to template-backed page responses
   Goal: make the primary app pages that already render through shared templates produce consistently readable source by default.
   Dependencies: Stage 1; existing route templates in [`templates/`](/home/wsl/v2/templates).
   Expected changes: route renderers that already rely on `render_page(...)` inherit the readable-output contract, and any template fragments that still collapse major structural sections get minor structural cleanup; planned conceptual touchpoints include representative page renderers in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py); no database changes.
   Verification approach: manual source inspection and targeted tests for representative shared-shell pages such as board, thread, activity, compose, and instance routes.
   Risks or open questions: test assertions should prove presentability without becoming brittle to harmless copy or spacing edits; some inline substituted fragments may still need explicit structure cleanup.
   Canonical components/API contracts touched: `render_page(...)`; route templates in `templates/`; existing HTML page-render tests.

3. Stage 3: Bring direct-response and host-side HTML pages onto the same standard
   Goal: eliminate the remaining single-line or inconsistent HTML paths outside the shared template renderer.
   Dependencies: Stage 1; direct HTML responses in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py); PHP host pages in [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php).
   Expected changes: refit Python-built refresh/error pages and PHP host fallback/rebuild pages so they follow the same readable-output structure as shared-shell pages; planned conceptual seams include `render_post_index_refresh_page(...) -> str`, `render_streamed_post_index_refresh_response(...) -> Iterable[bytes]`, the top-level server-error response path, and PHP helper renderers; no database changes.
   Verification approach: manual source inspection for representative direct-response pages plus focused tests for refresh/error/fallback responses where practical.
   Risks or open questions: streamed responses may need a lighter standard than fully buffered pages; PHP and Python outputs should stay recognizably aligned without forcing identical helper structure across languages.
   Canonical components/API contracts touched: direct-response HTML contract in `forum_web/web.py`; PHP host HTML page contract in `php_host/public/index.php`; request error/fallback response behavior.

4. Stage 4: Add regression coverage and presentability guardrails
   Goal: lock in readable-source behavior so future routes do not regress to collapsed or inconsistent HTML output.
   Dependencies: Stages 1-3.
   Expected changes: add focused assertions in existing page and host-response tests for readable structural output, and document the presentability expectation in the relevant planning or developer guidance if needed; no database changes.
   Verification approach: run targeted automated tests for representative template, direct-response, and PHP-host pages, then manually inspect a small cross-section of browser page source.
   Risks or open questions: coverage should target durable structure signals such as line breaks around major sections rather than exact formatting snapshots; developer guidance should stay short enough that it does not become a second style guide.
   Canonical components/API contracts touched: existing web/page tests under [`tests/`](/home/wsl/v2/tests); PHP host response tests; shared HTML presentability expectation for new page renderers.
