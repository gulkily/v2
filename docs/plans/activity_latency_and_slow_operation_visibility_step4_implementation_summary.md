## Stage 1 - Make slow activity requests visible and diagnosable
- Changes:
  - Added a recency-first `load_recent_slow_operations(...)` helper in `forum_core.operation_events` with the agreed `> 2s` threshold behavior for the project-info panel.
  - Updated the project-info “Recent slow operations” panel to use that slow-operation helper instead of the generic duration-first loader.
  - Added `/activity/` request metadata for `view` plus route-specific timing steps for repository-state load, activity-event load, event-card rendering, and git-status summary work.
- Verification:
  - Ran `python3 -m unittest /home/wsl/v2/tests/test_operation_events.py /home/wsl/v2/tests/test_request_operation_events.py /home/wsl/v2/tests/test_instance_info_page.py /home/wsl/v2/tests/test_site_activity_page.py`.
  - Ran a disposable Python smoke script that created a synthetic slow `GET /activity/` operation with `view=code` and confirmed `load_recent_slow_operations(...)` returns it.
- Notes:
  - The activity route now exposes enough step timing to identify whether repository loading, event loading, card rendering, or git-status work dominates the request.

## Stage 2 - Reduce avoidable activity-route work
- Changes:
  - Added a `/activity/?view=code` fast path that skips full repository-state loading and post-index building when the selected filter does not need canonical post resolution.
  - Reused already loaded post lists inside activity commit and moderation cards so the activity page no longer reloads `records/posts` repeatedly while rendering cards.
  - Preserved the existing `/activity/` route and filter output while making the code-filter request path materially narrower.
- Verification:
  - Ran `python3 -m unittest /home/wsl/v2/tests/test_request_operation_events.py /home/wsl/v2/tests/test_site_activity_page.py`.
  - Ran a disposable Python smoke script that requested `/activity/?view=code`, confirmed a `200 OK` response, confirmed the visible code-commit fallback text still rendered, and confirmed the recorded request steps do not include `activity_load_repository_state`.
- Notes:
  - The largest immediate win came from removing repeated `load_posts(...)` calls during activity-card rendering, not from changing the route contract.
