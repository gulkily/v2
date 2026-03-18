## Stage 1
- Goal: establish the shared moderation record and visible-state derivation helpers.
- Dependencies: approved Step 2; existing signing, identity, canonical post rules, and read surfaces.
- Expected changes: define the minimal canonical moderation record shape, add shared helpers for parsing and validating moderation records, add deterministic rules for moderator authorization against an instance-local allowlist, and add read-side helpers that derive active `hide`, `lock`, and `pin` state from visible moderation records; no write command or public log route yet.
- Verification approach: run the shared helpers against sample moderation records and sample signed moderator keys, confirm that the same input records always derive the same visible moderation state, and confirm unauthorized moderator fingerprints are rejected consistently.
- Risks or open questions:
  - choosing a moderation precedence rule that stays deterministic when multiple records target the same post or thread
  - keeping the initial allowlist mechanism simple without baking in long-term trust policy too early
- Canonical components/API contracts touched: moderation record shape; moderator authorization rules; deterministic visible-state derivation for `hide`, `lock`, `pin`, and `unpin`.

## Stage 2
- Goal: implement the signed moderation write contract end to end.
- Dependencies: Stage 1.
- Expected changes: add one explicit moderation write contract that accepts a signed moderation payload, verifies the signature, confirms the signer is an authorized moderator, validates the target and action shape, stores the moderation record under `records/moderation/`, and creates a deterministic git commit; planned helpers such as `validateModerationPayload(text) -> ModerationRecord`, `isAuthorizedModerator(fingerprint) -> bool`, and `storeModerationRecord(record) -> StoredModerationRecord`.
- Verification approach: submit valid signed `hide`, `lock`, `pin`, and `unpin` actions against existing posts and threads, confirm canonical moderation record files are created, confirm deterministic success responses and git commits are produced, and confirm invalid targets or unauthorized moderators return stable plain-text errors.
- Risks or open questions:
  - deciding whether moderation record IDs should be content-derived immediately or use a temporary deterministic generated ID for this loop
  - ensuring moderator writes remain deterministic if two moderation actions race against the same target
- Canonical components/API contracts touched: moderation write command envelope; signed moderation validation; canonical moderation storage and success/error response shapes.

## Stage 3
- Goal: expose the moderation read model through `get_moderation_log` and make the existing read surfaces honor active moderation state.
- Dependencies: Stage 2.
- Expected changes: add the plain-text `get_moderation_log` endpoint, derive a deterministic moderation log from visible moderation records, add a minimal read-only moderation log page if needed for the existing web UI, and update board/thread/post reads so active moderation state affects rendering in predictable ways, such as hidden content treatment, locked thread status, and pinned thread ordering; planned helpers such as `loadModerationLog(limit, before) -> list[ModerationRecord]`, `deriveThreadModerationState(thread_id) -> ThreadModerationState`, and `renderModerationLog(records) -> string`.
- Verification approach: request the moderation log and confirm stable ordering and formatting, confirm a hidden post or thread changes the relevant thread/index views predictably, confirm a locked thread exposes a visible locked status, confirm pinned threads sort predictably in board listings, and confirm repeated reads over unchanged repo state return byte-identical success output.
- Risks or open questions:
  - choosing the smallest visible UI treatment for hidden posts so this loop does not accidentally define the later soft-delete or tombstone semantics
  - keeping moderation-log pagination or cursor behavior deterministic enough for later multi-language parity fixtures
- Canonical components/API contracts touched: `get_moderation_log`; moderation log serialization; read-time application of `hide`, `lock`, `pin`, and `unpin` to current thread/index/post surfaces.
