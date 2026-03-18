## Stage 1
- Goal: broaden git commit collection and classify repository commits into explicit activity types.
- Dependencies: approved Step 2; current `ActivityEvent` model; existing git activity helpers in `forum_web/web.py`.
- Expected changes: replace the current content-only commit collection with repository-wide commit loading, add deterministic commit classification rules for at least content, moderation, and code commits based on touched paths, and expand fixed filter parsing to include `code`; planned contracts such as `fetch_recent_repository_commits(repo_root, *, limit: int) -> list[GitCommitEntry]`, `classify_commit_activity(commit) -> str`, and `activity_filter_mode_from_request(raw_mode) -> str`; no database changes.
- Verification approach: use helper-level tests with a disposable repo containing content, moderation, and code commits, then confirm commit classification and filter subsets match the touched-path rules.
- Risks or open questions:
  - deciding how commits that touch multiple areas should be classified in the first slice
  - keeping the classification rules simple enough to stay predictable
- Canonical components/API contracts touched: git-log commit helpers; merged `ActivityEvent` model; fixed activity filter parsing.

## Stage 2
- Goal: render code commits on `/activity/` and expose the fixed code-activity filter.
- Dependencies: Stage 1; current `/activity/` route, template, and mixed event-card rendering.
- Expected changes: extend `/activity/` so the default repository-history timeline can include code commits, add the `code` filter to the existing filter nav, and adapt commit-card rendering so code-only commits remain understandable without canonical post targets; planned contracts such as `render_activity_event_card(event, ...) -> str` with code-commit support and an expanded `render_activity_filter_nav(current_mode) -> str`.
- Verification approach: manually load `/activity/` in `all` and `code` modes, confirm code commits appear in the default timeline, and confirm the `code` filter isolates them while the snapshot panel remains intact.
- Risks or open questions:
  - deciding what minimal metadata a code commit card should show without turning into a diff browser
  - preserving readability when code commits and content commits share the same timeline
- Canonical components/API contracts touched: `/activity/`; `templates/activity.html`; commit-card rendering; filter navigation.

## Stage 3
- Goal: align labels, navigation expectations, and regression coverage with `/activity/` as a broader repository-history page.
- Dependencies: Stages 1-2; current activity and board-index tests.
- Expected changes: update page copy and any key navigation labels so `/activity/` clearly represents broader repository history, add focused regression tests for the new `code` filter and mixed-timeline behavior, and confirm compatibility routes such as `/moderation/` still land in the expected filtered experience; planned contracts such as expanded activity-page test fixtures and any small copy helpers needed for the broader page framing.
- Verification approach: request `/activity/` in `all`, `content`, `moderation`, and `code` modes; confirm the expected commit/event classes appear; run targeted unittest coverage for helper classification and page filtering.
- Risks or open questions:
  - balancing broader repository-history language with the existing user-facing activity copy
  - keeping tests stable when code commits do not have post-card targets
- Canonical components/API contracts touched: `/activity/` filter behavior; board-index activity navigation; helper and page-level activity tests.
