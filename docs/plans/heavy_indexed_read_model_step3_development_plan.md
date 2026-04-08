# Heavy Indexed Read Model Step 3: Development Plan

## Stage 1
- Goal: Define one indexed public-read contract for board/thread/profile data on top of the existing post index.
- Dependencies: Approved Step 2; current `post_index` schema and indexed helper surfaces.
- Expected changes: Add conceptual indexed read contracts for hot public pages, including board listings, thread detail payloads, and public-profile payloads; identify the minimum derived fields that must be authoritative in indexed reads; planned contracts such as `load_indexed_board_page(...)`, `load_indexed_thread_page(...)`, and `load_indexed_profile_page(...)` or equivalent shared helpers.
- Verification approach: Add focused contract tests proving the indexed payloads preserve current visibility, title-resolution, and profile-display semantics against representative fixtures.
- Risks or open questions:
- Moderation and title-update semantics may still depend on non-indexed helper paths and need a single indexed interpretation.
- Profile and merge-related public read semantics may require more indexed projection than board/thread reads.
- Canonical components/API contracts touched: `forum_core/post_index.py`; indexed username/profile helpers; canonical public read semantics in `forum_web/web.py` and `forum_web/profiles.py`.

## Stage 2
- Goal: Move the board index read path to the indexed contract.
- Dependencies: Stage 1.
- Expected changes: Refactor the board page and closely related lightweight board-read helpers to consume indexed board data instead of full request-time repository reconstruction; preserve the existing route shape, output semantics, and current post-index readiness path.
- Verification approach: Extend board-page tests and operator-facing timing checks to confirm equivalent page behavior with reduced request-time reconstruction.
- Risks or open questions:
- Board filtering and “last active” fields may still require non-indexed fallback if the indexed payload is incomplete.
- Canonical components/API contracts touched: board render path in `forum_web/web.py`; existing indexed root-post helpers in `forum_core/post_index.py`; board-page tests.

## Stage 3
- Goal: Move thread detail reads to the indexed contract.
- Dependencies: Stage 1; preferably after Stage 2 to reuse the same indexed read patterns.
- Expected changes: Refactor thread detail reads to load root/reply/title/visibility data from indexed helpers rather than rebuilding full repository state; keep compose/title-action links and moderation-visible behavior unchanged.
- Verification approach: Extend thread-page and task-thread read tests to prove rendered thread content still matches current public behavior while avoiding full request-time repository reconstruction.
- Risks or open questions:
- Reply ordering and hidden-post behavior must remain exactly aligned with current moderation rules.
- Task-thread read surfaces may expose extra metadata not present in the first indexed thread contract.
- Canonical components/API contracts touched: thread render path in `forum_web/web.py`; indexed thread/read helpers in `forum_core/post_index.py`; thread and task-thread page tests.

## Stage 4
- Goal: Move public profile reads to the indexed contract and align downstream consumers.
- Dependencies: Stage 1; may depend on follow-up indexed profile fields discovered in Stages 2-3.
- Expected changes: Refactor public profile reads and public profile-by-username resolution to consume indexed profile data; update PHP-native or other downstream prepared-read consumers to reuse the deeper indexed source rather than raw-record reconstruction for covered routes.
- Verification approach: Extend profile-route and PHP-native read tests to confirm public profile behavior remains correct and covered routes benefit from the indexed model.
- Risks or open questions:
- Self-only profile/account views may need to remain on the dynamic path in this slice.
- Username-route resolution and merged-profile display rules may require additional indexed readiness checks.
- Canonical components/API contracts touched: `forum_web/profiles.py`; profile render paths in `forum_web/web.py`; downstream prepared-read consumers such as `forum_core/php_native_reads.py`; profile and PHP-native tests.

## Stage 5
- Goal: Harden verification and operator visibility around the new indexed hot-read path.
- Dependencies: Stages 2-4.
- Expected changes: Add focused regression and operator-facing verification coverage showing covered hot routes no longer depend on full request-time reconstruction in the normal path; tighten slow-operation/readiness checks only where needed to prove the new route behavior.
- Verification approach: Run targeted route tests plus timing-oriented checks for covered routes and confirm slow-operation records stop being dominated by normal board/thread/profile reads.
- Risks or open questions:
- Performance assertions must stay resilient and avoid brittle wall-clock thresholds.
- Canonical components/API contracts touched: existing route tests; operator/timing surfaces; post-index readiness and hot-read verification helpers.
