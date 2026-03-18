## Problem
Signed writes currently store a fresh `.pub.asc` file each time a public key is submitted, even when that key is already visible elsewhere in the repository. The next slice should introduce one canonical deduplicated public-key storage model so operators stop accumulating repeated key files, while keeping signed verification, identity bootstrap, and existing signed record flows coherent.

## User Stories
- As a node operator, I want repeated signed submissions to reuse one stored public-key artifact so that repository growth is not dominated by duplicate key files.
- As a signed user, I want my later signed posts and signed actions to succeed without republishing the same public key into new files every time.
- As a reviewer, I want the repository to retain an explicit canonical copy of each visible public key so that signed records remain auditable.
- As a future backend implementer, I want the canonical key-storage rule to be deterministic so that other implementations can reproduce the same repository layout and lookup behavior.

## Core Requirements
- The slice must introduce one canonical deduplicated storage location for public keys that can be reused across signed record families.
- The slice must use a deterministic lookup rule for public keys so that repeated submissions of the same key resolve to the same stored artifact.
- Signed write flows must continue to require and verify submitted public keys at request time; this feature changes stored artifacts, not trust requirements.
- Signed records that currently create per-record public-key sidecars must instead reference the canonical stored key material after verification, while still storing signatures and canonical payload records.
- The slice must preserve explicit key publication when a genuinely new key first appears, and it must avoid historical backfill, repository-wide compaction, or broader identity-model changes.

## Shared Component Inventory
- Existing write APIs: reuse and extend the canonical signed write contracts for `/api/create_thread`, `/api/create_reply`, `/api/moderate`, `/api/link_identity`, `/api/merge_request`, and `/api/update_profile` because these already accept `public_key` input and produce stored signed records.
- Existing browser compose surfaces: reuse the current browser signing flow for thread, reply, moderation, merge-request, and profile-update submission because the client still submits the same signed material; no new browser interaction model is needed for this slice.
- Existing repository-backed identity surfaces: extend the current identity/bootstrap model so first-seen keys still become visible canonical repository artifacts, but later signed records reuse that canonical key store rather than writing new sidecars.
- Existing read surfaces: reuse current post, profile, moderation, merge-request, and repository readers; they may need to resolve canonical key references, but this slice should not introduce a separate public browsing surface for keys.

## Simple User Flow
1. A signed client submits a canonical payload, detached signature, and public key to an existing signed write endpoint.
2. The server verifies the signature against the submitted public key.
3. The server derives the canonical lookup for that public key and checks whether the key is already stored.
4. If the key is new, the server stores one canonical key artifact; if the key already exists, the server reuses the existing stored artifact.
5. The server stores the signed record and signature material, records the canonical key reference, and commits the write to git.

## Success Criteria
- Repeated signed submissions using the same public key no longer create a new per-record `.pub.asc` file each time.
- First-seen public keys are still stored explicitly in the repository and remain discoverable through canonical repository state.
- Existing signed write endpoints continue to accept and verify requests using the current request contract.
- At least posts plus the other existing signed record families all follow the same deterministic canonical key-storage rule.
- The resulting repository layout and lookup behavior are precise enough to serve as stable fixtures for later implementations.
