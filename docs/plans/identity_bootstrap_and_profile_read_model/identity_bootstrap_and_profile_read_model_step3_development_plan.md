## Stage 1
- Goal: establish the shared identity bootstrap and profile-derivation helpers.
- Dependencies: approved Step 2; existing signed posting flow, detached signature handling, and canonical post rules.
- Expected changes: define the minimal bootstrap post shape using the canonical post format, add shared helpers for deriving a stable `Identity-ID` from published key material, add deterministic rules for deciding whether visible bootstrap already exists for a key, and add plain-text profile summary serialization helpers; no profile page or posting-path integration yet.
- Verification approach: run the shared helpers against sample signed posts and sample public-key material, confirm that the same key always derives the same `Identity-ID`, confirm that bootstrap-detection rules are deterministic, and confirm that profile summaries serialize to stable plain-text output.
- Risks or open questions:
  - choosing an `Identity-ID` derivation rule that is simple enough for multi-language parity and stable across future file moves or storage refactors
  - making bootstrap-detection rules deterministic when the repository contains multiple signed posts for the same key
- Canonical components/API contracts touched: bootstrap post shape; `Identity-ID` derivation rules; deterministic plain-text profile summary format.

## Stage 2
- Goal: implement automatic identity bootstrap on the first signed post.
- Dependencies: Stage 1.
- Expected changes: extend the signed posting path so that when a user submits a signed thread or reply and no visible bootstrap exists yet for that key, the system automatically creates and stores bootstrap material alongside the accepted post, using the existing git-backed write flow; planned helpers such as `ensure_identity_bootstrap(posting_result, signer_key) -> IdentityBootstrapResult` and `buildBootstrapPayload(public_key) -> string`.
- Verification approach: submit a first signed post from a browser with a new local key, confirm the normal signed post is stored, confirm bootstrap material is also stored deterministically, confirm a stable `Identity-ID` can be derived from the resulting repository state, and confirm later signed posts from the same key do not create duplicate bootstrap material.
- Risks or open questions:
  - deciding whether bootstrap material should share the same git commit as the user's first post or use a second deterministic write
  - avoiding duplicate or conflicting bootstrap material if two first-post attempts race for the same key
- Canonical components/API contracts touched: signed `create_thread` and `create_reply` first-post behavior; automatic bootstrap creation rules; deterministic repository state after first signed write.

## Stage 3
- Goal: expose the identity read model through `get_profile` and a simple web profile view.
- Dependencies: Stage 2.
- Expected changes: add the plain-text `get_profile` endpoint, derive profile summaries from visible bootstrap material and visible signed posts associated with the same `Identity-ID`, add a minimal read-only web profile page, and link the new profile surface from existing signed-post reads where appropriate; planned helpers such as `loadProfile(identity_id) -> ProfileSummary | None` and `renderProfileSummary(summary) -> string`.
- Verification approach: request a profile for a newly bootstrapped identity, confirm the plain-text API and web page reflect the same derived identity summary, confirm missing identities return stable `not_found` behavior, and confirm repeated reads over unchanged repo state return byte-identical success output.
- Risks or open questions:
  - deciding how much activity summary to include in the first profile view without accidentally introducing ranking, moderation, or profile-edit semantics
  - keeping profile lookup deterministic when related posts have been soft-deleted or hard-purged later
- Canonical components/API contracts touched: `get_profile`; profile summary derivation from visible records; read-only user/profile web view and linking behavior.
