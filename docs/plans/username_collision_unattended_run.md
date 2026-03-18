# Username Collision Unattended Run

Purpose: unattended execution log for the username-collision FDP checklist.

Uses:

- [unattended_fdp_guidelines.md](/home/wsl/v2/docs/plans/unattended_fdp_guidelines.md)
- [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
- [username_collision_working_notes.md](/home/wsl/v2/docs/username_collision_working_notes.md)

## Run Metadata

- Feature area: username collisions, canonical username roots, merge ergonomics, and revocation
- Checklist doc: [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
- Run date: 2026-03-17
- Operator: unattended
- Branch: `username-collision-unattended`
- Target loop range: Loops 1-10

## Controlling Docs

- [username_collision_working_notes.md](/home/wsl/v2/docs/username_collision_working_notes.md)
- [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
- [unattended_fdp_guidelines.md](/home/wsl/v2/docs/plans/unattended_fdp_guidelines.md)
- [forum_feature_splitting_checklist.md](/home/wsl/v2/docs/plans/forum_feature_splitting_checklist.md)
- [code_style_guidelines.md](/home/wsl/v2/docs/plans/code_style_guidelines.md)

## Locked Defaults

- Username collisions should prefer acceptance plus disambiguation over rejection.
- Canonical username root is the identity or merged set whose username claim appears first in repository commit chronology.
- The deciding claim event is the first visible signed profile update that claims the username.
- Public username rendering should show one canonical root plus `other users with this name`.
- Username overlap alone is sufficient for auto-issued merge requests for now.
- One approved merge should attach the incoming identity to the whole resolved set.
- Notifications should attach to the existing `My profile` navigation entry rather than a full inbox.
- Merge revocation should use a one-sided append-only `revoke_merge` style record with immediate effect.
- Revocation should deactivate a specific approved merge edge, then current state should be recomputed from the remaining active edges using existing graph rules.
- Canonical records remain authoritative; SQLite cache state is derived convenience data only.
- One SQLite file is the default cache direction unless there is a concrete reason to split caches later.
- When in doubt, prefer the current graph-derived visible state over adding special-case username policy.
- Avoid reopening settled product questions during this run unless two controlling docs conflict.

## Commit Plan

- Minimum commit rule: at least one commit per completed loop
- Preferred commit rule: one commit per meaningful internal step when a loop naturally splits
- Commit naming convention:
  - loop-level commit: `username-collision loop <N>: <summary>`
  - step-level commit: `username-collision loop <N> step <M>: <summary>`
- Verification rule: each loop should leave behind targeted tests or equivalent focused verification for the visible behavior it changes
- Any exceptions:
  - none initially

## Execution Defaults

- Run loops in checklist order unless a stop condition forces a pause.
- Prefer the smallest visible, testable slice for each loop.
- Prefer extending existing codepaths, routes, cache files, and templates over adding parallel systems.
- Do not batch multiple unrelated loops into one commit.
- Update this run log after each completed loop.

## Loop Checklist

- [x] Loop 1: Identity graph and username-root SQLite cache
  - Goal: cache the derived identity graph, current username claims, and canonical username roots in the existing SQLite cache database.
  - Smallest intended visible result: a rebuildable SQLite model that can answer current root/non-root username ownership deterministically.
  - Controlling docs:
    - [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
    - [username_collision_working_notes.md](/home/wsl/v2/docs/username_collision_working_notes.md)
  - Notes:
    - default to extending the existing SQLite cache rather than adding a new DB file

- [x] Loop 2: Canonical username root read model
  - Goal: make the canonical username-root rule explicit in the read layer.
  - Smallest intended visible result: one deterministic source of truth for root set and `other users with this name`.
  - Controlling docs:
    - [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
    - [username_collision_working_notes.md](/home/wsl/v2/docs/username_collision_working_notes.md)
  - Notes:
    - chronology should follow repository commit history, not payload timestamps

- [x] Loop 3: Public profile rendering for duplicate usernames
  - Goal: render the canonical-root model clearly on profile pages and `/user/<username>`.
  - Smallest intended visible result: users can see one canonical root and an `other users with this name` section.
  - Controlling docs:
    - [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
    - [username_collision_working_notes.md](/home/wsl/v2/docs/username_collision_working_notes.md)
  - Notes:
    - no new handle-decoration scheme should be introduced in this loop

- [x] Loop 4: Auto-issued merge requests for likely self-merges
  - Goal: smooth the common same-user multi-device flow.
  - Smallest intended visible result: claiming an already-used username can auto-create or near-auto-create a merge request targeting the canonical root or root set.
  - Controlling docs:
    - [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
    - [username_collision_working_notes.md](/home/wsl/v2/docs/username_collision_working_notes.md)
  - Notes:
    - username overlap alone is sufficient evidence for the first version

- [x] Loop 5: `My profile` notification badge and merge queue
  - Goal: surface account and merge actions without building a full inbox.
  - Smallest intended visible result: the existing nav shows pending merge and username-related actions that need attention.
  - Controlling docs:
    - [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
    - [username_collision_working_notes.md](/home/wsl/v2/docs/username_collision_working_notes.md)
  - Notes:
    - keep the UX attached to `My profile`, not a new inbox route

- [x] Loop 6: One-approval-to-whole-set merge activation
  - Goal: make merge approval semantics match the working policy.
  - Smallest intended visible result: one approval merges the incoming identity with the whole resolved set.
  - Controlling docs:
    - [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
    - [username_collision_working_notes.md](/home/wsl/v2/docs/username_collision_working_notes.md)
  - Notes:
    - preserve existing graph-resolution approach rather than inventing a second merge state model

- [x] Loop 7: One-sided append-only `revoke_merge`
  - Goal: add the simplest recovery path for mistaken merges.
  - Smallest intended visible result: a signed one-sided revocation changes current graph state immediately.
  - Controlling docs:
    - [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
    - [username_collision_working_notes.md](/home/wsl/v2/docs/username_collision_working_notes.md)
  - Notes:
    - reference whichever prior merge approval or active edge is easiest to implement while remaining deterministic

- [ ] Loop 8: Revocation-aware profile and attribution readback
  - Goal: make split results visible everywhere current identity state is rendered.
  - Smallest intended visible result: profile and attribution surfaces reflect the graph after revocation.
  - Controlling docs:
    - [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
    - [username_collision_working_notes.md](/home/wsl/v2/docs/username_collision_working_notes.md)
  - Notes:
    - follow current graph-derived visible state without special-case backfill rules

- [ ] Loop 9: Suggested self-merge dismissal or suppression
  - Goal: prevent repetitive false-positive merge suggestions.
  - Smallest intended visible result: users have a low-friction way to stop repeated unwanted same-name suggestions.
  - Controlling docs:
    - [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
    - [username_collision_working_notes.md](/home/wsl/v2/docs/username_collision_working_notes.md)
  - Notes:
    - keep the first version narrow; no broad trust or reputation system

- [ ] Loop 10: Duplicate-name list scaling and presentation polish
  - Goal: keep `other users with this name` usable when many unrelated claimants exist.
  - Smallest intended visible result: the list stays readable under high duplicate count.
  - Controlling docs:
    - [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
    - [username_collision_working_notes.md](/home/wsl/v2/docs/username_collision_working_notes.md)
  - Notes:
    - keep this loop cosmetic and usability-focused, not policy-expanding

## Per-Loop Output Log

Use one short entry per completed loop.

### Loop 1

- Status: completed
- What landed:
  - extended the existing SQLite cache schema with identity-membership, active-merge-edge, current-username-claim, and username-root tables
  - populated those tables during post-index rebuild using the existing identity context plus repository commit chronology for username-root selection
  - added helper loaders for indexed identity members and username roots
  - added focused regression coverage for the new cache content
- Visible result:
  - the repo now has one cached derived source for current identity-membership and canonical username-root state without changing public read behavior yet
- Commits:
  - `53e4065` `username-collision loop 1: cache identity graph and username roots`
- Tests or verification:
  - `python -m unittest tests.test_post_index`
  - result: `Ran 14 tests ... OK`
- New deferred questions:
  - none
- Checklist/doc updates:
  - marked Loop 1 complete in [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)

### Loop 2

- Status: completed
- What landed:
  - added cache-backed username-root claim loaders for the existing SQLite index
  - added a canonical username-root read-model helper in [profiles.py](/home/wsl/v2/forum_web/profiles.py)
  - switched username-route profile resolution to use the cached root decision rather than the old duplicate-name rejection path
  - updated route regressions to assert canonical-root behavior for duplicate current usernames
- Visible result:
  - `/user/<username>` now resolves to the canonical root profile when multiple current identities share the same username
- Commits:
  - `b5e82ee` `username-collision loop 2: add canonical username root read model`
- Tests or verification:
  - `python -m unittest tests.test_post_index tests.test_username_profile_route`
  - result: `Ran 19 tests ... OK`
- New deferred questions:
  - none
- Checklist/doc updates:
  - marked Loop 2 complete in [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)

### Loop 3

- Status: completed
- What landed:
  - added visible `Other Users With This Name` rendering on profile pages
  - used the cached username-root and username-claim state to populate the peer list
  - extended duplicate-name route tests to verify the new visible section on both `/user/<username>` and canonical identity profile pages
- Visible result:
  - users can now open the canonical root profile for a duplicate current username and immediately see the other identities that currently share that name
- Commits:
  - `b1a8b3e` `username-collision loop 3: render duplicate username peers`
- Tests or verification:
  - `python -m unittest tests.test_username_profile_route`
  - `python -m unittest tests.test_post_index tests.test_username_profile_route`
  - result: `Ran 20 tests ... OK`
- New deferred questions:
  - none
- Checklist/doc updates:
  - marked Loop 3 complete in [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)

### Loop 4

- Status: completed
- What landed:
  - added a direct `Likely Self-Merge` suggestion on non-root duplicate-name profile pages
  - linked the suggestion straight into the existing signed merge-request action flow, targeted at the canonical username root
  - added route regression coverage for the direct self-merge suggestion
- Visible result:
  - a user who lands on their non-root duplicate-name profile can request a merge with the canonical root directly from that page instead of hunting through merge management
- Commits:
  - `3cf724c` `username-collision loop 4: suggest direct self-merges`
- Tests or verification:
  - `python -m unittest tests.test_username_profile_route`
  - `python -m unittest tests.test_post_index tests.test_username_profile_route`
  - result: `Ran 21 tests ... OK`
- New deferred questions:
  - none
- Checklist/doc updates:
  - marked Loop 4 complete in [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)

### Loop 5

- Status: completed
- What landed:
  - extended the existing `My profile` nav asset to fetch merge-management counts for the stored identity
  - made the nav link show `My profile (N)` when pending username or merge attention exists
  - pointed the nav link at merge management when those notifications are present
  - added focused asset tests for count parsing and merge-page targeting
- Visible result:
  - the shared nav now surfaces username and merge attention directly on `My profile` without adding a full inbox
- Commits:
  - `a7429d0` `username-collision loop 5: add profile nav merge notifications`
- Tests or verification:
  - `python -m unittest tests.test_profile_nav_asset`
  - result: `Ran 3 tests ... OK`
- New deferred questions:
  - none
- Checklist/doc updates:
  - marked Loop 5 complete in [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)

### Loop 6

- Status: completed
- What landed:
  - expanded approved merge links across the requester and target resolved sets instead of only the directly approved pair
  - made target-side approval valid from any member of the target's current resolved set
  - iterated identity resolution so approved merge requests can attach an incoming identity to the whole resolved set
  - added unit and API coverage for set-wide merge activation
- Visible result:
  - one approved merge now joins the incoming identity to the whole currently resolved target set rather than only the directly named target identity
- Commits:
  - `fa5be50` `username-collision loop 6: merge whole resolved sets`
- Tests or verification:
  - `python -m unittest tests.test_merge_requests tests.test_merge_management_api tests.test_merge_request_submission`
  - result: `Ran 11 tests ... OK`
- New deferred questions:
  - none
- Checklist/doc updates:
  - marked Loop 6 complete in [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)

### Loop 7

- Status: completed
- What landed:
  - added append-only `revoke_merge` handling to merge-request state derivation so revocations disable previously active merges without deleting history
  - allowed one-sided immediate revocation through the merge-request submission API for signers already in the merged resolved set
  - exposed `revoke merge` actions on approved merge-management rows and wired the existing signing flow to that action
  - added focused regression coverage for revoke state derivation, API submission, and merge-management rendering
- Visible result:
  - users can now revoke an active merge immediately from merge management, and the current graph drops that merge while keeping the original approval records in history
- Commits:
  - pending
- Tests or verification:
  - `python -m unittest tests.test_merge_requests tests.test_merge_request_submission tests.test_merge_management_page`
  - result: `Ran 14 tests ... OK`
- New deferred questions:
  - none
- Checklist/doc updates:
  - marked Loop 7 complete in [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)

## Stop Conditions Hit

Leave empty if none.

- 

## End State

- Completed loops:
  - Loop 1
  - Loop 2
  - Loop 3
  - Loop 4
  - Loop 5
  - Loop 6
  - Loop 7
- Deferred loops:
  - Loops 8-10
- New unresolved questions:
  - none from Loops 1-7
- Docs updated:
  - [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md)
  - [username_collision_unattended_run.md](/home/wsl/v2/docs/plans/username_collision_unattended_run.md)
- Tests run:
  - `python -m unittest tests.test_post_index`
  - `python -m unittest tests.test_post_index tests.test_username_profile_route`
  - `python -m unittest tests.test_username_profile_route`
  - `python -m unittest tests.test_post_index tests.test_username_profile_route`
  - `python -m unittest tests.test_profile_nav_asset`
  - `python -m unittest tests.test_merge_requests tests.test_merge_management_api tests.test_merge_request_submission`
  - `python -m unittest tests.test_merge_requests tests.test_merge_request_submission tests.test_merge_management_page`

## Handoff Summary

Write a short summary of what the unattended run accomplished and what still needs a human decision.
