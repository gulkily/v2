## Stage 1
- Goal: broaden the activity event model so git commits can be classified beyond content-only changes.
- Dependencies: approved Step 2; existing `ActivityEvent` model; current `fetch_recent_commits(...)` helper limited to `records/posts`.
- Expected changes: extend the git-activity helper layer so it can collect recent repository commits across content, moderation, and code paths, classify commits deterministically by touched files, and expose a new code-activity class while preserving the current merged event shape; planned contracts such as `fetch_recent_repository_commits(repo_root, *, limit: int) -> list[GitCommitEntry]`, `classify_commit_activity(commit) -> str`, and an expanded `activity_filter_mode_from_request(raw_mode) -> str`; no database changes.
- Verification approach: build helper-level tests in a disposable repo with content, moderation, and code commits, then confirm the classification and filter subsets match the touched-file rules.
- Risks or open questions:
  - deciding how to classify commits that touch multiple areas such as both code and `records/posts`
  - keeping the classification deterministic without growing into a free-form tagging system
- Canonical components/API contracts touched: git-log commit helpers; merged `ActivityEvent` model; fixed activity filter parsing.

## Stage 2
- Goal: render code commits on `/activity/` and expose a fixed code-activity filter.
- Dependencies: Stage 1; current `/activity/` route and template; existing commit-card rendering.
- Expected changes: extend the activity page rendering so the default timeline can include code commits, add a fixed `code` filter alongside the existing filter modes, and adapt commit-card rendering so code-only commits remain intelligible even without canonical post targets; planned contracts such as `render_activity_event_card(event, ...) -> str` with code-commit support and `render_activity_filter_nav(current_mode) -> str` including the new filter.
- Verification approach: manually load `/activity/` in all and code-only modes, confirm code commits appear in the default timeline, and confirm the code filter isolates them without removing the existing repository snapshot panel.
- Risks or open questions:
  - deciding what minimal metadata a code commit card needs when there is no post permalink target
  - avoiding a UI that feels like a raw git log instead of a curated repository-history page
- Canonical components/API contracts touched: `/activity/`; `templates/activity.html`; commit-card rendering; merged filter navigation.

## Stage 3
- Goal: align navigation and regression coverage with the broader repository-history surface.
- Dependencies: Stages 1-2; existing activity and board-index tests.
- Expected changes: update focused tests for mixed repository-history ordering and the new code filter, confirm compatibility paths such as `/moderation/` still land in the expected filtered view, and adjust any copy or navigation labels needed so `/activity/` clearly represents broader repository history rather than only content-plus-moderation activity; planned contracts such as test helpers for mixed commit classes and any small label-copy updates in the activity page/header.
- Verification approach: request `/activity/` in all, content, moderation, and code modes; confirm the expected event classes appear; run targeted unittest coverage for helper classification and page filtering.
- Risks or open questions:
  - keeping tests stable when code commits do not have canonical post-card targets
  - balancing broader repository-history language with existing activity-page expectations
- Canonical components/API contracts touched: `/activity/` filter behavior; board-index navigation labels; helper and page-level activity tests.
