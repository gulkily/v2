## Problem
The forum can now attach signed identities to posts and expose profile reads, but moderation is still missing as a first-class part of repository state. The next slice should add the smallest useful moderation record model so a trusted moderator can sign an auditable action, store it in git-backed text records, change what the public instance shows, and expose a deterministic moderation log without pulling in bans, soft-delete policy, or hard-purge behavior.

## User Stories
- As a moderator, I want to issue a signed moderation action against a post or thread so that the public instance can change visible state without editing content files directly.
- As a reader, I want thread and index views to reflect active moderation state so hidden or locked content is rendered consistently.
- As a reviewer, I want moderation actions to be inspectable as canonical text records in git so moderation remains auditable and forkable.
- As a future backend implementer, I want moderation write and read behavior to be explicit and deterministic so later implementations can reproduce the same results.

## Core Requirements
- The slice must define a minimal canonical moderation record shape stored separately from posts.
- The slice must support signed `hide`, `lock`, `pin`, and `unpin` moderation actions with explicit target references.
- The slice must add one explicit moderation write contract that validates moderator authorization, target existence, and action shape before storing a moderation record.
- The slice must add a deterministic `get_moderation_log` read surface.
- The slice must make the current read surfaces honor visible moderation state at least for thread/index rendering and thread interaction status.
- The slice must keep moderator authorization simple for now, such as an instance-local allowlist of trusted moderator fingerprints.
- The slice must avoid bans, scheduled expiration, tombstone semantics, hard-purge behavior, key-merge trust policy, or richer moderator UI flows.

## Shared Component Inventory
- Existing UI surfaces: reuse the current thread, post, board index, and profile views, extending them only as much as needed to show moderation effects and a simple moderation log.
- Existing API surfaces: add `get_moderation_log` and one moderation write contract while keeping existing read and write routes intact.
- Existing data surfaces: reuse detached signatures, identity IDs, and canonical text storage while adding `records/moderation/` for signed moderation records.
- Existing backend surfaces: build on the current signing, identity, and git-backed write helpers so moderation records are validated, stored, and committed through the same deterministic machinery.

## Simple User Flow
1. A trusted moderator submits a signed moderation action against a post or thread through the moderation write contract.
2. The server verifies the signature, confirms the signer is allowed to moderate locally, validates the target and action shape, and stores the canonical moderation record in repository storage.
3. The server creates a git commit for the moderation action and returns a stable plain-text success response.
4. Readers request a thread, board index, or moderation log.
5. The server derives visible moderation state from the stored records and returns views that reflect active `hide`, `lock`, `pin`, and `unpin` actions, plus a deterministic moderation log.

## Success Criteria
- A trusted moderator can create a signed moderation record without editing repository files by hand.
- Accepted moderation actions are stored as canonical text files under a moderation records directory and committed to git.
- `get_moderation_log` returns a deterministic plain-text list of visible moderation records.
- Thread and index reads change in predictable ways when a relevant moderation action is present.
- The moderation contract and visible-state behavior are specific enough to serve as fixtures for later non-Python implementations.
