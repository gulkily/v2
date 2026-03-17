## Problem
The forum can resolve identities after reciprocal merge records exist, but it does not yet help a user discover likely related identities, request a merge, or review incoming approvals. The next slice should add the smallest useful workflow for same-username discovery across visible username history plus explicit merge approval by both identities or by a moderator, without turning the loop into full notifications, username ownership policy, or moderator dispute handling.

## User Stories
- As a signed user, I want to see other visible identities that have used the same username as me so that I can find accounts I may want to merge.
- As a signed user, I want to send a merge request to another identity so that the merge workflow does not require out-of-band coordination first.
- As a signed user, I want to review and approve or dismiss incoming merge requests so that no merge completes without my explicit consent.
- As a moderator, I want to approve a merge request so that clearly related identities can still be consolidated when direct two-sided coordination is impractical.
- As a reader, I want merged identities to resolve to one logical profile only after both sides approve so that identity consolidation remains conservative and understandable.
- As a future backend implementer, I want merge-request behavior to be explicit and deterministic so that other implementations can reproduce the same visible state from repository records.

## Core Requirements
- The slice must let a signed user discover other visible identities that overlap with any current or historical username in the visible profile-update history.
- The slice must require explicit approval from both participating identities before a merge becomes active, unless a moderator approval path for the request is present and defined.
- The slice must let a signed user review incoming merge requests and dismiss requests they do not want to act on.
- The slice must let a moderator review and approve eligible merge requests through an explicit moderation-aware path.
- The slice must preserve the current conservative rule that matching usernames are only merge suggestions, not automatic proof of shared ownership.
- The slice must avoid unique-username reservation, broad moderator-adjudicated identity disputes, generic inbox infrastructure, or automatic merges based on name overlap.

## Shared Component Inventory
- Existing profile-update record family: extend it as the canonical visible username-history source because it already records signed display-name changes for each identity and avoids inventing a second naming ledger.
- Existing identity-link/identity-resolution model: extend the canonical merge workflow rather than introducing a parallel account-link system, because merged profiles already resolve through signed identity-link state.
- Existing moderation identity and signed moderation surfaces: extend the canonical moderator authority model rather than inventing a separate trusted-admin channel for merge approvals.
- Existing web profile surface `/profiles/<identity-slug>`: reuse as the public read surface with at most a link into merge management, because the feature needs signer-specific workflow rather than a second public profile design.
- New web merge-management surface: add one dedicated page for same-name discovery, outgoing requests, and incoming approvals because no existing page cleanly handles signer-specific merge workflow.
- Existing API discovery surface `/api/`: extend it to advertise any new merge-request write/read routes because `/api/` is already the canonical capability list.

## Simple User Flow
1. A signed user opens the merge-management page for one of their identities.
2. The page shows other visible identities whose current or historical usernames overlap with that identity's visible username history.
3. The user submits a signed merge request to one candidate identity.
4. The target identity later sees that pending request in the same merge-management flow and either approves it or dismisses it, or a moderator reviews and approves it through the moderation-aware path.
5. If both identities explicitly approve, or if the defined moderator approval rule is satisfied, the system resolves them as one logical profile set; otherwise they remain separate.

## Success Criteria
- A signed user can see candidate identities derived from visible historical username overlap for the identity they are managing.
- A one-sided request alone does not activate a merge; the merge becomes active only after the full configured approval condition is satisfied.
- Incoming merge requests are visible to the target identity and can be dismissed without merging.
- Moderator approval is explicit, auditable, and limited to the merge-request workflow rather than acting as a general identity rewrite tool.
- After mutual approval, profile reads through either identity resolve to the same logical profile using the existing identity-resolution model.
- The feature remains narrow enough that duplicate usernames still behave as suggestions rather than exclusive claims or automatic merges.
