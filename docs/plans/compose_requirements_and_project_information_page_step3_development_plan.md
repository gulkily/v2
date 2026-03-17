## Stage 1
- Goal: add clear compose-time requirements and ASCII rationale to the shared compose experience.
- Dependencies: approved Step 2; existing `render_compose_page(...)` path; current compose template and browser normalization behavior.
- Expected changes: extend the compose page shell so thread, reply, and task compose flows all show concise requirements and limitations near the form, including the ASCII constraint and rationale around human readability, easier handling of canonical text records, and reduced Unicode-obfuscation risk; planned contracts such as shared compose-guidance markup in `templates/compose.html` and any small helper context additions in `forum_web/web.py`; no new routes.
- Verification approach: request representative compose pages and confirm the requirements and rationale are visible without opening advanced panels, and that the copy aligns with the current normalization-status behavior.
- Risks or open questions:
  - keeping the guidance prominent without making the compose page feel overloaded
  - ensuring the rationale matches actual browser-side normalization behavior and server-side expectations
- Canonical components/API contracts touched: `render_compose_page(...)`; `templates/compose.html`; compose-page test coverage.

## Stage 2
- Goal: replace the current instance-info framing with a broader project-information page that keeps key facts and adds explanatory FAQ-style content.
- Dependencies: Stage 1; current `/instance/` route; existing instance metadata loader and template.
- Expected changes: adapt the current instance-info route and template so the page is framed as project information rather than only deployment facts, preserve the current public metadata and derived repository facts as one section, and add a compact explanatory FAQ-style section covering anticipated orientation questions; planned contracts such as updated page title or heading copy, evolved `templates/instance_info.html` content structure or a replacement template, and the existing `load_instance_info(...)` data source.
- Verification approach: load the renamed project-information page and confirm both the carried-forward facts and the new explanatory sections render together in one coherent page.
- Risks or open questions:
  - deciding how much of the existing instance-facts emphasis should remain above the fold
  - keeping the FAQ-style content concise enough to stay readable inside one page
- Canonical components/API contracts touched: `/instance/`; instance-information template/content structure; current public metadata rendering.

## Stage 3
- Goal: align navigation labels, page copy, and regression coverage with the compose-guidance and project-information changes.
- Dependencies: Stages 1-2; current compose, board-index, and instance-info tests; existing shared navigation labels.
- Expected changes: update key navigation or action labels so users encounter the renamed project-information concept consistently, add focused regression tests for compose guidance visibility and the renamed information-page framing, and confirm the preserved instance facts plus FAQ-style content remain covered; planned contracts such as updated primary or board-index labels, expanded compose-page tests, and renamed instance-page expectations.
- Verification approach: request compose, board-index, and project-information surfaces; confirm the new copy is visible and coherent; run targeted unittest coverage for compose guidance, navigation labels, and the renamed information page.
- Risks or open questions:
  - balancing clearer user-facing terminology with the existing `/instance/` route contract
  - keeping copy assertions stable while still proving the explanatory content exists
- Canonical components/API contracts touched: shared navigation labels; compose-page copy/tests; instance or project-information page tests.
