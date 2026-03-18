## Stage 1
- Goal: extend the git activity read model so commit entries carry richer summary metadata and GitHub-link inputs.
- Dependencies: approved Step 2; current `GitCommitEntry` model; existing repository-history helpers in `forum_web/web.py`.
- Expected changes: broaden the git-log helper layer so each activity commit includes the metadata needed to explain what happened, including touched-file lists, explicit `.md` file highlights, area counts or summaries, canonical target extraction where applicable, author, timestamp, short-hash support, and the deterministic inputs needed to build an outbound GitHub commit URL; planned contracts such as an expanded `GitCommitEntry`, `fetch_recent_repository_commits(repo_root, *, limit: int) -> list[GitCommitEntry]`, and `github_commit_url_for(commit_id, repo_root) -> str | None`; no new routes.
- Verification approach: use helper-level tests with disposable repos containing content, moderation, docs, and code commits, then confirm the richer commit metadata, `.md` detection, canonical target derivation, and GitHub-link inputs are derived predictably from git state.
- Risks or open questions:
  - deciding which commit facts are high-signal enough to include without making the cards noisy
  - choosing a GitHub URL source that stays deterministic across local environments
- Canonical components/API contracts touched: `GitCommitEntry`; git-log activity helpers; outbound GitHub link helper.

## Stage 2
- Goal: render richer commit detail and GitHub links inside the existing `/activity/` card layout.
- Dependencies: Stage 1; current `/activity/` route; existing mixed activity-card rendering; current activity page template.
- Expected changes: adapt commit-card rendering so content and code commits show clearer “what changed” detail, including touched-file lists, explicit `.md` updates, area summaries, subject, short hash, author, timestamp, change type, canonical targets when present, and a GitHub link when a deterministic URL can be built; keep the card layout concise enough to remain a timeline rather than a diff browser; planned contracts such as `render_commit_card(commit, posts, identity_context, *, activity_kind: str) -> str` with richer metadata support.
- Verification approach: manually load `/activity/` in representative filter modes, confirm the richer commit facts appear on cards in the expected sections, and confirm the GitHub link target is rendered consistently for commit entries.
- Risks or open questions:
  - preserving readability when commit cards gain more metadata
  - deciding how to present the GitHub link when the remote page may not exist yet
- Canonical components/API contracts touched: `/activity/`; commit-card rendering; `templates/activity.html` card stack.

## Stage 3
- Goal: align configuration assumptions, page copy, and regression coverage around the richer commit-card experience.
- Dependencies: Stages 1-2; existing activity helper tests; current activity and board-index page tests.
- Expected changes: update any activity-page copy needed so the richer cards and outbound links feel intentional, add focused regression tests for touched-file rendering, `.md` highlights, area summaries, canonical target display, and GitHub-link generation, and confirm existing filters still work with the enhanced cards; planned contracts such as helper tests for GitHub URL generation and page tests asserting enriched commit cards.
- Verification approach: request `/activity/` in multiple filter modes; confirm richer commit cards render as expected; run targeted unittest coverage for helper metadata extraction, `.md` detection, GitHub URL generation, and page rendering.
- Risks or open questions:
  - keeping tests stable when the GitHub link is deterministic but the remote page is outside local control
  - avoiding copy that implies the app verifies remote GitHub availability
- Canonical components/API contracts touched: activity page copy; commit-card rendering tests; helper and page-level activity coverage.
