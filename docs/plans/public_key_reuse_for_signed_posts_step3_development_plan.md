1. Stage 1: Define the canonical public-key store contract
Goal: Establish one deterministic repository location and lookup rule for deduplicated public keys, plus the shared helper contract that all signed write paths will use.
Dependencies: Approved Step 2 only.
Expected changes: Add a shared concept such as `store_or_reuse_public_key(*, repo_root: Path, public_key_text: str) -> StoredPublicKeyRef`; define the canonical path rule for first-seen versus already-known keys; define how signed records will persist or derive a canonical key reference without requiring per-record `.pub.asc` copies.
Verification approach: Manual helper-level checks that the same public key text always resolves to the same canonical repository path and that first-seen versus repeated-key behavior is deterministic.
Risks or open questions:
- The main design choice is where the canonical key reference lives for record families that currently infer signer information from a sibling `.pub.asc` file.
- The canonical lookup key must stay stable across future identity-link and key-rotation behavior.
Canonical components/API contracts touched: shared signing/storage helper contract; repository layout for canonical stored public keys; submission result field that reports the stored public-key path.

2. Stage 2: Refactor signed write paths to reuse canonical key storage
Goal: Make every existing signed write family store signatures plus canonical key references instead of fresh per-record public-key sidecars.
Dependencies: Stage 1.
Expected changes: Thread the shared public-key-store helper through signed post, moderation, identity-link, merge-request, and profile-update submission/storage flows; update conceptual signatures such as `store_post(..., public_key_ref: StoredPublicKeyRef | None)` and equivalent record-family helpers; keep request-time `public_key` verification unchanged.
Verification approach: Manual API smoke checks for new-key and repeated-key submissions across at least post plus one non-post signed record family, confirming repeated submissions reuse one canonical key artifact.
Risks or open questions:
- The change spans several near-duplicate write paths, so the plan must avoid drifting into inconsistent per-family behavior.
- Dry-run responses must remain deterministic even though they now point at canonical key paths.
Canonical components/API contracts touched: `/api/create_thread`, `/api/create_reply`, `/api/moderate`, `/api/link_identity`, `/api/merge_request`, `/api/update_profile`; canonical signed storage helpers and success/error text responses.

3. Stage 3: Update read models to resolve canonical key references
Goal: Keep repository reads, identity derivation, and signed-record loading correct after per-record `.pub.asc` files stop being the source of truth.
Dependencies: Stage 2.
Expected changes: Update record loaders and identity helpers to resolve signer key material through the canonical key-store contract or persisted canonical key reference; add conceptual helpers such as `resolve_public_key_for_record(record_path: Path) -> Path | None` and `fingerprint_from_stored_public_key_ref(ref) -> str`; ensure current post, moderation, merge-request, profile-update, and identity-link readers still derive signer identity deterministically.
Verification approach: Manual smoke checks that existing read surfaces still load signed records, derive the same signer fingerprints for unchanged logical content, and continue to render profile/attribution links correctly.
Risks or open questions:
- Some record families currently depend on sibling file naming rather than explicit signer metadata, so this stage may require a minimal canonical metadata addition.
- Historical records with per-record sidecars must remain readable alongside the new canonical key-store layout.
Canonical components/API contracts touched: forum-core record loaders; identity fingerprint derivation helpers; current post/profile/moderation/merge-request read surfaces.

4. Stage 4: Add regression coverage and operator-facing repository expectations
Goal: Lock in deterministic behavior for repeated-key reuse, mixed old/new records, and canonical public-key path reporting.
Dependencies: Stages 1-3.
Expected changes: Add targeted tests for helper-level key reuse, signed post and non-post write reuse, and read compatibility with both legacy sidecars and the new canonical key-store model; update operator-facing repository-layout docs where they describe signed artifact storage.
Verification approach: Run targeted tests plus a manual regression pass for signed posting, profile updates, moderation, and one merge/identity-link action using an already-known key.
Risks or open questions:
- Mixed-format repositories are the main regression risk, especially if some readers still assume record-local `.pub.asc` paths.
- Documentation must describe the new canonical-key layout precisely enough for later implementations.
Canonical components/API contracts touched: signed-write tests, repository-layout docs, and plain-text success responses that expose public-key paths.
