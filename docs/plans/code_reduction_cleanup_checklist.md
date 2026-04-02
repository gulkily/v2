# Code Reduction Cleanup Checklist

This checklist turns the initial reduction review into an ordered execution plan.

The intent is to remove code safely, starting with high-confidence dead code and low-risk consolidation, then moving toward structural simplification where the regression risk is higher.

Current focus: Phase 6, reviewing feature-slice ownership boundaries and simplifying the next high-duplication slice.

## Working Rules

- Do not delete anything based on grep alone.
- Pair each cleanup slice with focused regression coverage.
- Prefer removing an entire concept over shaving a few lines from many places.
- When two implementations overlap, choose one canonical owner before consolidating.
- Keep cleanup changes small enough that failures point to one decision.

## Phase 1: High-Confidence Dead Code

- [x] Remove unused helper `get_thread_auto_reply_model()` from [`forum_cgi/auto_reply.py`](/home/wsl/v2/forum_cgi/auto_reply.py).
- [x] Remove unused helper `index_moderation_records()` from [`forum_core/moderation.py`](/home/wsl/v2/forum_core/moderation.py).
- [x] Remove unused helper `php_host_config_example_path()` from [`forum_core/php_host_setup.py`](/home/wsl/v2/forum_core/php_host_setup.py).
- [x] Remove unused helper `list_snapshots_by_type()` from [`forum_core/php_native_reads_db.py`](/home/wsl/v2/forum_core/php_native_reads_db.py).
- [x] Remove unused helper `increment_php_native_read_counter()` from [`forum_core/php_native_reads_db.py`](/home/wsl/v2/forum_core/php_native_reads_db.py).
- [x] Remove unused dataclass `IndexedIdentityMemberRow` from [`forum_core/post_index.py`](/home/wsl/v2/forum_core/post_index.py).
- [x] Remove unused dataclass `IndexedMergeEdgeRow` from [`forum_core/post_index.py`](/home/wsl/v2/forum_core/post_index.py).
- [x] Run focused tests for the touched modules after the deletion pass.

Phase 1 verification:
- Focused tests passed:
  - `python3 -m unittest tests.test_thread_auto_reply tests.test_php_native_reads tests.test_thread_title_updates tests.test_merge_management_api tests.test_post_index.PostIndexSchemaTests tests.test_post_index.PostIndexAuthorHelpersTests`
- Broader check note:
  - `python3 -m unittest tests.test_post_index` currently contains an unrelated `MergeRequestState` constructor mismatch in `tests.test_post_index.PostIndexBuildTests.test_rebuild_post_index_caches_identity_members_username_claims_and_roots`.

## Phase 2: Test Harness Consolidation

- [x] Create a shared test helper module for temporary repo setup, record writing, and WSGI request execution.
- [x] Consolidate repeated `setUp()` and `tearDown()` tempdir patterns used across page and API tests.
- [x] Consolidate repeated `write_record()` helpers used across record-driven tests.
- [x] Consolidate repeated `get()` and `request()` WSGI helpers used across page and API tests.
- [x] Consolidate repeated `run_git()` and command-runner helpers where the semantics are the same.
- [x] Collapse byte-vs-text request duplication by making one helper support both response modes.
- [x] Update the heaviest repeated test files first:
  - [`tests/test_compose_thread_page.py`](/home/wsl/v2/tests/test_compose_thread_page.py)
  - [`tests/test_compose_reply_page.py`](/home/wsl/v2/tests/test_compose_reply_page.py)
  - [`tests/test_board_index_page.py`](/home/wsl/v2/tests/test_board_index_page.py)
  - [`tests/test_profile_update_submission.py`](/home/wsl/v2/tests/test_profile_update_submission.py)
  - [`tests/test_thread_title_update_submission.py`](/home/wsl/v2/tests/test_thread_title_update_submission.py)
- [x] Run the affected test slices after each helper migration batch.

Phase 2 verification:
- Focused tests passed:
  - `python3 -m unittest tests.test_compose_thread_page tests.test_compose_reply_page tests.test_board_index_page tests.test_profile_update_submission tests.test_thread_title_update_submission`

## Phase 3: Shared Flag and Environment Parsing Cleanup

- [x] Inventory env-flag parsing helpers and duplicated truthy parsing logic across Python and PHP surfaces.
- [x] Choose one canonical Python helper for env-flag evaluation and route new code through it.
- [x] Reduce repeated inline truthy parsing where it does not need route-local behavior.
- [x] Review whether any feature flags are effectively permanent and can be removed rather than preserved.
- [x] Add or update focused tests before collapsing any flag behavior.

Phase 3 verification:
- Focused tests passed:
  - `python3 -m unittest tests.test_merge_feature_flag tests.test_profile_update_feature_flag tests.test_proof_of_work tests.test_thread_title_updates tests.test_thread_auto_reply`
- Review note:
  - This phase kept the existing feature flags in place and only centralized their Python-side parsing.

## Phase 4: Shared Page Shell Consolidation

- [x] Review the duplicated page-shell rendering logic in:
  - [`forum_web/templates.py`](/home/wsl/v2/forum_web/templates.py)
  - [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php)
- [x] Decide the canonical owner for shared shell content:
  - Shared shell copy and script metadata now live in [`templates/page_shell_content.json`](/home/wsl/v2/templates/page_shell_content.json), with Python and PHP continuing to render runtime-specific HTML around that shared data.
- [x] Consolidate duplicated nav markup, footer markup, username-claim CTA markup, and shared script tags.
- [x] Keep behavior and output stable while removing copy-pasted markup.
- [x] Re-run PHP host tests and route-level shell tests after each consolidation step.

Phase 4 verification:
- Focused tests passed:
  - `python3 -m unittest tests.test_board_index_page tests.test_compose_thread_page tests.test_account_setup_initial_render tests.test_php_host_cache tests.test_php_host_missing_config_page`

## Phase 5: Route and Asset Surface Review

- [x] Verify every asset route in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py) is still needed by either page rendering, PHP host support, or tests.
- [x] Verify the PHP cache/static-html layer only special-cases assets and routes that are still part of the supported surface.
- [x] Remove asset or route branches only after confirming there is no template, PHP, or test dependency.
- [x] Re-check whether any compatibility-only paths can be collapsed into canonical routes.

Phase 5 verification:
- Focused tests passed:
  - `python3 -m unittest tests.test_compose_thread_page tests.test_site_css_asset tests.test_profile_key_viewer_asset tests.test_account_key_actions_asset tests.test_merge_management_page tests.test_username_profile_route tests.test_task_priorities_page tests.test_php_host_cache tests.test_llms_txt`
- Review note:
  - Asset dispatch now comes from [`templates/asset_routes.json`](/home/wsl/v2/templates/asset_routes.json), which also defines the PHP-cacheable subset.

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
