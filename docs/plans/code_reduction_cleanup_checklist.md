# Code Reduction Cleanup Checklist

This checklist turns the initial reduction review into an ordered execution plan.

The intent is to remove code safely, starting with high-confidence dead code and low-risk consolidation, then moving toward structural simplification where the regression risk is higher.

## Working Rules

- Do not delete anything based on grep alone.
- Pair each cleanup slice with focused regression coverage.
- Prefer removing an entire concept over shaving a few lines from many places.
- When two implementations overlap, choose one canonical owner before consolidating.
- Keep cleanup changes small enough that failures point to one decision.

## Phase 1: High-Confidence Dead Code

- [ ] Remove unused helper `get_thread_auto_reply_model()` from [`forum_cgi/auto_reply.py`](/home/wsl/v2/forum_cgi/auto_reply.py).
- [ ] Remove unused helper `index_moderation_records()` from [`forum_core/moderation.py`](/home/wsl/v2/forum_core/moderation.py).
- [ ] Remove unused helper `php_host_config_example_path()` from [`forum_core/php_host_setup.py`](/home/wsl/v2/forum_core/php_host_setup.py).
- [ ] Remove unused helper `list_snapshots_by_type()` from [`forum_core/php_native_reads_db.py`](/home/wsl/v2/forum_core/php_native_reads_db.py).
- [ ] Remove unused helper `increment_php_native_read_counter()` from [`forum_core/php_native_reads_db.py`](/home/wsl/v2/forum_core/php_native_reads_db.py).
- [ ] Remove unused dataclass `IndexedIdentityMemberRow` from [`forum_core/post_index.py`](/home/wsl/v2/forum_core/post_index.py).
- [ ] Remove unused dataclass `IndexedMergeEdgeRow` from [`forum_core/post_index.py`](/home/wsl/v2/forum_core/post_index.py).
- [ ] Run focused tests for the touched modules after the deletion pass.

## Phase 2: Test Harness Consolidation

- [ ] Create a shared test helper module for temporary repo setup, record writing, and WSGI request execution.
- [ ] Consolidate repeated `setUp()` and `tearDown()` tempdir patterns used across page and API tests.
- [ ] Consolidate repeated `write_record()` helpers used across record-driven tests.
- [ ] Consolidate repeated `get()` and `request()` WSGI helpers used across page and API tests.
- [ ] Consolidate repeated `run_git()` and command-runner helpers where the semantics are the same.
- [ ] Collapse byte-vs-text request duplication by making one helper support both response modes.
- [ ] Update the heaviest repeated test files first:
  - [`tests/test_compose_thread_page.py`](/home/wsl/v2/tests/test_compose_thread_page.py)
  - [`tests/test_compose_reply_page.py`](/home/wsl/v2/tests/test_compose_reply_page.py)
  - [`tests/test_board_index_page.py`](/home/wsl/v2/tests/test_board_index_page.py)
  - [`tests/test_profile_update_submission.py`](/home/wsl/v2/tests/test_profile_update_submission.py)
  - [`tests/test_thread_title_update_submission.py`](/home/wsl/v2/tests/test_thread_title_update_submission.py)
- [ ] Run the affected test slices after each helper migration batch.

## Phase 3: Shared Flag and Environment Parsing Cleanup

- [ ] Inventory env-flag parsing helpers and duplicated truthy parsing logic across Python and PHP surfaces.
- [ ] Choose one canonical Python helper for env-flag evaluation and route new code through it.
- [ ] Reduce repeated inline truthy parsing where it does not need route-local behavior.
- [ ] Review whether any feature flags are effectively permanent and can be removed rather than preserved.
- [ ] Add or update focused tests before collapsing any flag behavior.

## Phase 4: Shared Page Shell Consolidation

- [ ] Review the duplicated page-shell rendering logic in:
  - [`forum_web/templates.py`](/home/wsl/v2/forum_web/templates.py)
  - [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php)
- [ ] Decide the canonical owner for shared shell content:
  - Python-generated fragments reused by PHP, or
  - a deliberately separate PHP shell with a narrower supported surface.
- [ ] Consolidate duplicated nav markup, footer markup, username-claim CTA markup, and shared script tags.
- [ ] Keep behavior and output stable while removing copy-pasted markup.
- [ ] Re-run PHP host tests and route-level shell tests after each consolidation step.

## Phase 5: Route and Asset Surface Review

- [ ] Verify every asset route in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py) is still needed by either page rendering, PHP host support, or tests.
- [ ] Verify the PHP cache/static-html layer only special-cases assets and routes that are still part of the supported surface.
- [ ] Remove asset or route branches only after confirming there is no template, PHP, or test dependency.
- [ ] Re-check whether any compatibility-only paths can be collapsed into canonical routes.

## Phase 6: Feature Slice Simplification

- [ ] Review the boundaries between `forum_web`, `forum_cgi`, and `forum_core` for overlapping responsibilities.
- [ ] Identify feature slices that have read/write/formatting logic split more than necessary.
- [ ] Consolidate only after choosing a clear owner module for each concern.
- [ ] Prioritize slices with the most branching or duplication:
  - profile updates
  - merge requests
  - moderation
  - thread title updates
  - PHP native reads

## Phase 7: Documentation and Planning Cleanup

- [ ] Remove or update docs that refer to deleted helpers, old branches, or superseded workflows.
- [ ] Check `docs/plans` notes for references to removed implementation details that could mislead future work.
- [ ] Keep planning docs that still record useful design intent; delete only obsolete operational clutter.

## Verification Checklist For Each Cleanup PR

- [ ] Confirm the target is truly unused or intentionally redundant.
- [ ] Make the smallest coherent removal or consolidation.
- [ ] Run only the focused tests needed for the touched area.
- [ ] Check for import fallout, route fallout, and test-helper drift.
- [ ] Write a short note in the PR or commit message describing what was removed and why it was safe.

## Recommended Execution Order

1. Phase 1 dead-code removals
2. Phase 2 test harness consolidation
3. Phase 3 flag/env parsing cleanup
4. Phase 4 shared page shell consolidation
5. Phase 5 route and asset review
6. Phase 6 feature-slice simplification
7. Phase 7 docs cleanup

## Expected Outcome

- Smaller production surface area
- Lower test maintenance cost
- Less shell and route duplication between Python and PHP paths
- Clearer ownership boundaries across modules
- Fewer stale helpers and lower future cleanup cost
