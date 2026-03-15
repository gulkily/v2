## Stage 1
- Goal: establish the shared identity-link record model and deterministic identity-resolution helpers.
- Dependencies: approved Step 2; existing identity bootstrap/profile model, detached signature handling, and canonical text storage rules.
- Expected changes: define the minimal canonical identity-link record family for `rotate_key` and `merge_identity`, add shared helpers for parsing and validating identity-link records, add deterministic rules for resolving visible key-backed identities into one logical identity set, and add a canonical identity-selection rule for linked sets; no write command or public read-surface refactor yet.
- Verification approach: run the shared helpers against sample bootstrap records plus sample identity-link records, confirm that the same visible repo state always resolves to the same linked identity sets, confirm reciprocal merge requirements behave deterministically, and confirm canonical identity selection is stable.
- Risks or open questions:
  - choosing a canonical identity-selection rule that stays stable across later repo growth and still leaves room for future federation policy
  - keeping merge activation deterministic when only one side of a reciprocal merge is visible or when rotation chains become long
- Canonical components/API contracts touched: identity-link record shape; deterministic identity-resolution rules; canonical identity selection for linked sets.

## Stage 2
- Goal: implement the signed identity-link write contract end to end.
- Dependencies: Stage 1.
- Expected changes: add one explicit identity-link write contract that accepts a signed `rotate_key` or `merge_identity` payload, verifies the signature, validates referenced identities or keys, stores the canonical record under an identity-links records directory, and creates a deterministic git commit; planned helpers such as `validateIdentityLinkPayload(text) -> IdentityLinkRecord`, `verifyIdentityLinkAuthority(record) -> ResolutionAuthority`, and `storeIdentityLinkRecord(record) -> StoredIdentityLinkRecord`.
- Verification approach: submit valid signed `rotate_key` and reciprocal `merge_identity` actions against existing visible identities, confirm canonical identity-link files and detached signature/public-key sidecars are created, confirm deterministic success responses and git commits are produced, and confirm invalid signatures or unknown referenced identities return stable plain-text errors.
- Risks or open questions:
  - deciding the smallest acceptable authority rule for who may assert a merge or rotation in this loop without dragging in moderator-trust policy
  - ensuring identity-link writes remain deterministic if concurrent records reference the same identities in conflicting ways
- Canonical components/API contracts touched: identity-link write command envelope; signed merge/rotation validation; canonical identity-link storage and success/error response shapes.

## Stage 3
- Goal: expose the resolved identity model through `get_profile` and current attribution surfaces.
- Dependencies: Stage 2.
- Expected changes: update profile derivation so `get_profile` and the web profile page resolve through linked identity sets rather than single-fingerprint identities, make profile URLs for non-canonical member identities resolve to the same logical profile, and update post plus moderation attribution to point at resolved canonical identities; planned helpers such as `resolveIdentity(identity_id_or_alias) -> ResolvedIdentity | None`, `loadResolvedProfile(identity_id) -> ProfileSummary | None`, and `canonicalizeIdentityReference(identity_id) -> IdentityID`.
- Verification approach: request profiles through both canonical and member identity IDs after a valid rotation or merge, confirm the API and web profile view return the same resolved summary, confirm existing signed posts and moderation records now link to the canonical profile target, and confirm repeated reads over unchanged repo state return byte-identical success output.
- Risks or open questions:
  - deciding how much historical bootstrap/key detail to include in the first resolved profile summary without accidentally dragging in profile-edit semantics
  - keeping profile resolution predictable when linked identities span records that later become soft-deleted or hard-purged
- Canonical components/API contracts touched: resolved `get_profile`; canonical profile URL behavior for linked identities; read-time attribution resolution for signed posts and moderation records.
