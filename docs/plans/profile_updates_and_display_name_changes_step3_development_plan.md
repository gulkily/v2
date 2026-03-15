## Stage 1
- Goal: define the canonical profile-update record model and deterministic current-name resolution rules.
- Dependencies: approved Step 2; existing identity bootstrap/profile read model; existing linked-identity resolution from Loop 14.
- Expected changes: define one canonical signed profile-update record family under a dedicated records directory such as `records/profile-updates/`; add shared helpers for parsing, loading, and validating the minimal `set_display_name` action; define deterministic selection rules for the current visible display name across a resolved identity set, with planned helpers such as `parseProfileUpdatePayload(text) -> ProfileUpdateRecord`, `loadProfileUpdateRecords(repo_root) -> list[ProfileUpdateRecord]`, and `resolveCurrentDisplayName(identity_id, identity_context, profile_updates) -> ResolvedDisplayName | None`.
- Verification approach: run the shared helpers against sample single-identity and linked-identity profile-update records, confirm identical repository state always resolves to the same current display name, and confirm identities without updates still use the existing fallback label.
- Risks or open questions:
  - choosing the smallest valid display-name normalization rule without turning this loop into full username policy
  - choosing a deterministic winner when multiple visible member identities in one linked set publish competing updates
- Canonical components/API contracts touched: profile-update record shape; deterministic display-name resolution rules; fallback-label behavior for identities with no profile updates.

## Stage 2
- Goal: implement the signed profile-update write contract end to end.
- Dependencies: Stage 1.
- Expected changes: add one explicit API/CLI-first `update_profile` write contract that accepts a signed profile-update payload, verifies the signature, validates that the signer is allowed to publish an update for the resolved identity, stores the canonical record plus detached signature/public-key sidecars, and creates a deterministic git commit; planned helpers such as `submit_profile_update(payload_text, repo_root, *, dry_run, signature_text, public_key_text) -> ProfileUpdateSubmissionResult`, `validateProfileUpdateAuthority(record, signer_identity_id, identity_context) -> ResolutionAuthority`, and `storeProfileUpdateRecord(record) -> StoredProfileUpdateRecord`.
- Verification approach: submit valid signed updates for both a single-key identity and a linked identity set, confirm canonical files plus sidecars are written with deterministic preview/success output and git commits, and confirm signer mismatch or unknown identities return stable plain-text errors.
- Risks or open questions:
  - deciding the narrowest authority rule that still lets any linked member identity update the shared resolved profile name
  - keeping write results deterministic if multiple profile updates are submitted close together
- Canonical components/API contracts touched: `update_profile` command envelope; signed profile-update validation; canonical profile-update storage and success/error response shapes.

## Stage 3
- Goal: extend the resolved profile read model and plain-text profile API with the current display name.
- Dependencies: Stage 2.
- Expected changes: update the profile summary model so `get_profile` includes the current display name plus the existing fallback label context, load visible profile-update records alongside bootstraps and identity links, and resolve the same current display name for any member identity in a linked set; planned helpers such as `loadProfileSummary(identity_id) -> ProfileSummary | None`, `resolveProfileDisplayName(summary) -> str`, and `displayNameFallback(summary) -> str`.
- Verification approach: request `get_profile` through canonical and member identity IDs before and after a valid profile update, confirm identical resolved summaries for linked aliases, and confirm identities with no update still produce deterministic output.
- Risks or open questions:
  - deciding how much fallback-label detail to keep in the first text API without making the profile summary noisy
  - preserving deterministic output ordering while introducing the new profile-update input stream
- Canonical components/API contracts touched: `ProfileSummary`; `get_profile`; deterministic plain-text profile summary fields for current display name and fallback behavior.

## Stage 4
- Goal: expose the resolved display name consistently on current web profile and attribution surfaces.
- Dependencies: Stage 3.
- Expected changes: update `/profiles/<identity-slug>` so the profile page headline shows the current display name while retaining canonical identity details, update signed post and moderation attribution labels to prefer the resolved display name while keeping canonical profile links stable, and extend `/api/` discovery text to list the new `update_profile` route.
- Verification approach: render thread, post, profile, and moderation pages after a valid profile update, confirm all linked aliases show the same display name and profile target, and confirm identities without updates still render the existing fingerprint-derived fallback label.
- Risks or open questions:
  - avoiding reader confusion when two unrelated identities choose the same display name
  - keeping unsigned posts and non-profile surfaces unchanged while signed attribution labels evolve
- Canonical components/API contracts touched: `/profiles/<identity-slug>`; signed author/moderator attribution labels on thread/post/moderation pages; `/api/` command discovery text.
