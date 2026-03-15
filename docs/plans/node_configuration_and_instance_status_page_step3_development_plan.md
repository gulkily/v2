## Stage 1
- Goal: define the canonical public instance-facts model and source boundaries before adding the page.
- Dependencies: approved Step 2; current runtime env loading; current repository-backed read-only app.
- Expected changes: add one shared instance-info helper module or equivalent read-side contract that gathers the public fact set from canonical local sources, defines stable labels for missing/unset values, and separates runtime-derived facts from tracked instance metadata; planned helpers such as `load_instance_info(repo_root: Path) -> InstanceInfo`, `resolve_commit_id(repo_root: Path) -> str | None`, and `render_public_value(value: str | None) -> str`.
- Verification approach: run focused helper tests against a disposable repo root and confirm the public fact set can be produced deterministically when values are present, partially present, or absent.
- Risks or open questions:
  - choosing the canonical source for facts not currently represented in `.env`, such as retention policy, install date, or admin/contact text
  - deciding how much git-state failure should surface publicly versus falling back to an explicit “unavailable” value
- Canonical components/API contracts touched: shared instance-info read contract; runtime env surfaces in `forum_core/runtime_env.py`; git/repository identity of the current instance.

## Stage 2
- Goal: add the dedicated public instance status/configuration route and render it through the existing read-only page stack.
- Dependencies: Stage 1; existing `forum_read_only.web` route and template patterns.
- Expected changes: extend the read-only web app with one canonical route for instance information, add a dedicated template for grouped instance facts, and render the page through the existing shared page shell without introducing a second UI system; planned helpers such as `render_instance_info_page() -> str` and any route-dispatch addition needed to serve `/instance/` or the chosen canonical path.
- Verification approach: manually request the new route in a local test repo and confirm the page renders the full fact set, shows explicit placeholders for unset values, and preserves the current read-only page structure.
- Risks or open questions:
  - choosing a route name that is clear and durable enough to remain the canonical public destination
  - grouping policy, contact, and deployment facts clearly without letting the page drift into an admin dashboard
- Canonical components/API contracts touched: `forum_read_only.web`; `templates/base.html`; new instance-info template; shared read-only routing contract.

## Stage 3
- Goal: make the new page obvious from the main board index and keep the board-level navigation coherent.
- Dependencies: Stage 2; current board index action row.
- Expected changes: extend the board index action row with a direct link to the instance info page, keep the new destination aligned with the existing public navigation language, and update any hero or section copy only as much as needed to make the page discoverable.
- Verification approach: load the board index and confirm the new link is visible in the main action row, uses the canonical route, and reaches the instance info page in one click.
- Risks or open questions:
  - adding visibility without overcrowding the small primary action row
  - choosing wording that communicates “instance facts/configuration” to technical users without sounding like a private admin area
- Canonical components/API contracts touched: `templates/board_index.html`; board-index public navigation contract; instance-page route naming.

## Stage 4
- Goal: cover the new instance-info surface with focused tests and document the canonical public fact contract.
- Dependencies: Stages 1-3.
- Expected changes: add page tests for the new route and board-index link, add helper-level tests around missing-value and source-resolution behavior, and update the relevant operator or developer docs to describe where public instance facts come from and how they appear on the public page.
- Verification approach: run targeted unittest modules for the new helper and page coverage, manually open the board index and instance page in a disposable repo configuration, and confirm the documented fact sources match the rendered behavior.
- Risks or open questions:
  - keeping tests stable if commit-ID lookup depends on local git state
  - documenting the operator-facing source of truth clearly enough that future changes do not create duplicate config surfaces
- Canonical components/API contracts touched: `tests/` read-only page coverage; shared instance-info helper contract; public instance-info documentation surface.
