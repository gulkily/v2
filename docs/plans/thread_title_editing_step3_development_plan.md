## Stage 1
- Goal: Define the canonical thread-title update record shape and authority policy, including the shared feature flag for permissive any-user renames.
- Dependencies: Approved Step 2 only.
- Expected changes: add a thread-title update domain model plus parse/load/resolve helpers; planned contracts such as `ThreadTitleUpdateRecord`, `parse_thread_title_update_text(...)`, `load_thread_title_updates(...)`, `resolve_current_thread_title(...)`, and `thread_title_any_user_edit_enabled(...) -> bool`; define conceptual validation inputs for owner, operator, and permissive-flag cases.
- Verification approach: add focused parser and policy tests covering valid payloads, malformed payloads, owner/operator authorization, and permissive-flag authorization changes.
- Risks or open questions:
  - The record shape must be broad enough for both owner and operator edits without introducing ambiguous authority metadata.
  - Title normalization rules need to stay compatible with existing single-line ASCII subject expectations.
- Canonical components/API contracts touched: new thread-title update record family; shared env flag helper pattern; canonical title-resolution contract used by thread reads.

## Stage 2
- Goal: Add one canonical signed submission path for thread-title changes.
- Dependencies: Stage 1.
- Expected changes: add a submission service parallel to profile updates, including validation, signature checks, record storage, and commit-backed persistence; planned contracts such as `submit_thread_title_update(...)`, `validate_thread_title_update_record(...)`, `store_thread_title_update_record(...)`, `/api/update_thread_title`, and matching plain-text success/error rendering.
- Verification approach: submit dry-run and real signed title updates in a disposable repo, then confirm accepted writes return stable response fields and rejected writes fail for unauthorized or malformed requests.
- Risks or open questions:
  - Authorization must resolve thread ownership consistently for signed roots and operator actions.
  - The new endpoint should reuse existing signing and commit semantics instead of drifting into a custom write contract.
- Canonical components/API contracts touched: `forum_cgi` signed-write pipeline; `/api/update_thread_title`; API discovery text in `/api/` and `/llms.txt`.

## Stage 3
- Goal: Make every thread-title read surface resolve one current title instead of reading only the root subject.
- Dependencies: Stages 1-2.
- Expected changes: extend canonical thread loading or derived read helpers so title resolution can overlay the original root subject; planned contracts such as `resolved_thread_title(thread, updates, ...) -> str` or a `current_title` field on the read model; conceptually update post-index/native-read helpers to surface the resolved title without rewriting stored root posts.
- Verification approach: create threads plus later title updates, then confirm the board index, thread page, task/planning thread pages, text API, and PHP/native read path all show the same current title.
- Risks or open questions:
  - Read paths must stay aligned across Python and PHP/native hosts.
  - Index or cached-read integration should stay incremental and avoid a second competing title source.
- Canonical components/API contracts touched: `forum_web.repository`; `forum_web.web`; `forum_web.api_text`; `forum_core.php_native_reads`; post-index or other derived read contracts that currently expose `subject`.

## Stage 4
- Goal: Add a browser-visible title-change affordance and payload-generation flow that reuses the canonical signed submission model.
- Dependencies: Stages 2-3.
- Expected changes: add one thread-title change page or action surface linked from eligible thread views, plus browser-signing support for the new command; planned contracts such as `render_thread_title_update_page(...)`, `render_api_update_thread_title(...)`, and browser-signing command metadata for `update_thread_title`; expose eligibility messaging that reflects owner/operator policy and the permissive flag state.
- Verification approach: manually open a thread, submit a signed title change through the browser flow, and confirm redirect/readback behavior for both allowed and disallowed users under each flag state.
- Risks or open questions:
  - The UI must not imply broader thread-edit capabilities than title change alone.
  - Eligibility messaging should remain truthful even when the browser has a key that does not control the current thread.
- Canonical components/API contracts touched: thread page action area; shared compose/profile-update style browser-signing assets; canonical `/api/update_thread_title` write flow.

## Stage 5
- Goal: Add regression coverage for authorization, feature-flag behavior, and resolved-title consistency.
- Dependencies: Stages 1-4.
- Expected changes: add targeted tests for owner renames, operator renames, permissive-flag any-user renames, unauthorized failures when the flag is off, and consistent readback across HTML and text surfaces; include at least one test that the original root post subject remains unchanged while the resolved title changes.
- Verification approach: run targeted unit and request tests for the new record parser, submission endpoint, thread page, board/task indexes, API text surfaces, and feature-flag helpers.
- Risks or open questions:
  - Coverage should prefer policy and read consistency assertions over brittle markup snapshots.
  - The test set should stay narrow enough to avoid turning this slice into a full moderation-policy rewrite.
- Canonical components/API contracts touched: thread-title update tests; feature-flag helper tests; thread/index/API regression suite for resolved title behavior.
