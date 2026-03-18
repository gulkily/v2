# Username Collision FDP Loop Checklist

Purpose: turn the current username-collision and identity-merge decisions into a practical ordered sequence of FDP loops.

This is a cross-feature planning doc, not a Step 1-4 trail for one specific loop yet.

## Already-Landed Foundation

- [x] Identity bootstrap and profile read model
- [x] Profile updates and display-name changes
- [x] Identity merge and key rotation records
- [x] Merge requests and same-name identity discovery
- [x] Username-based joined profile routing
- [x] Browser profile/account hub affordances
- [x] SQLite derived post index foundation

These loops already give the repo the base needed for collision-handling work: visible usernames, mergeable identities, merge workflow, profile pages, and a derived SQLite cache.

## Recommended Loop Order

- [x] Loop 1: Identity graph and username-root SQLite cache
  - Goal: cache the derived identity graph, current username claims, and canonical username roots in the existing SQLite cache database.
  - Includes: tables for active merge edges, revoked merge edges or their effective state, current username claims, canonical root resolution, and cache refresh hooks on relevant writes.
  - Why first: later loops need one deterministic place to read current username-root and graph state cheaply.

- [x] Loop 2: Canonical username root read model
  - Goal: make the canonical username-root rule explicit in the read layer.
  - Includes: earliest username-claim by git commit chronology, root-set resolution, and deterministic `other users with this name` derivation.
  - Why next: this locks the core semantics before adding more UI behavior.

- [x] Loop 3: Public profile rendering for duplicate usernames
  - Goal: render the new canonical-root model clearly on profile pages and `/user/<username>`.
  - Includes: canonical root rendering, `other users with this name` section, conservative duplicate-name handling, and ordering for the other-identities list.
  - Why next: this is the first visible user-facing result of the new policy.

- [ ] Loop 4: Auto-issued merge requests for likely self-merges
  - Goal: smooth the common same-user multi-device flow.
  - Includes: automatic or near-automatic merge-request issuance when a new identity claims a username already used elsewhere, targeting the canonical root or root set.
  - Why here: once root ownership is clear in the read model, auto-request creation has a stable target.

- [ ] Loop 5: `My profile` notification badge and merge queue
  - Goal: surface account and merge actions without building a full inbox.
  - Includes: nav-attached notification state, pending merge approvals, and other username/account actions that need attention.
  - Why here: auto-issued merge requests need a visible place to show up.

- [ ] Loop 6: One-approval-to-whole-set merge activation
  - Goal: make merge approval semantics match the working policy.
  - Includes: approval by one member of the resolved set activates the merge for the whole set, plus regression coverage for set-wide graph updates.
  - Why here: notification and auto-request flows should feed into the final merge semantics users actually experience.

- [ ] Loop 7: One-sided append-only `revoke_merge`
  - Goal: add the simplest recovery path for mistaken merges.
  - Includes: canonical `revoke_merge` record shape, immediate effect, deterministic reference to the revoked approval or active edge, graph recomputation from remaining active edges, and updated root/other rendering after split.
  - Why here: merge ergonomics should not expand further without a recovery mechanism.

- [ ] Loop 8: Revocation-aware profile and attribution readback
  - Goal: make split results visible everywhere current identity state is rendered.
  - Includes: post attribution, moderation attribution, profile pages, `/user/<username>`, and notification state after revocation.
  - Why here: revocation must not exist only in the data model; readers need to see the updated state consistently.

- [ ] Loop 9: Suggested self-merge dismissal or suppression
  - Goal: prevent repetitive false-positive merge suggestions without adding a broad new trust system.
  - Includes: simple `not me` handling or equivalent suppression for repeated same-name suggestions.
  - Why here: once auto-issued requests exist, the product needs a low-friction way to reduce noise.

- [ ] Loop 10: Duplicate-name list scaling and presentation polish
  - Goal: keep `other users with this name` usable when many unrelated claimants exist.
  - Includes: ordering policy, truncation or collapse behavior, and any lightweight explanation of why another identity appears in the list.
  - Why here: this is polish on top of the settled root/non-root behavior, not a prerequisite for correctness.

## Deferred Questions

These should stay out of the first implementation sequence unless they become blocking:

- stronger warning language and account-history evidence on merge approval
- whether canonical root should ever move away from earliest claim if the root becomes inactive
- whether merged-set username changes should automatically propagate in every surface
- whether revoked identities should keep old merge-history items in the nav notification area
- whether duplicate-name situations should affect posting attribution text differently from profiles/navigation
- whether moderators need extra username/graph debug visibility
- whether users should be able to request merge without shared username overlap

## Recommended First Three Loops

- [ ] First: identity graph and username-root SQLite cache
- [ ] Second: canonical username root read model
- [ ] Third: public profile rendering for duplicate usernames

That sequence should produce the smallest coherent slice of the new policy:

- one cached source of truth for current identity and username-root state
- one deterministic root/non-root decision rule
- one visible public rendering of duplicate-name behavior
