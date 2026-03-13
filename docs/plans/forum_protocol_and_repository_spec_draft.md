# Forum Protocol And Repository Spec Draft

## Status
- Draft supporting spec for architecture planning.
- Purpose: make the v1 repository layout, canonical record form, and CGI/API contract concrete enough for parallel implementations in Perl and Python.
- This document is more detailed than the Step 2 feature description, but it is still a planning artifact rather than implementation code.

## 1. Version 1 Scope
- Read surfaces: board index, thread view, post permalink, user/profile view, moderation log.
- Write surfaces: create thread, create reply.
- Ordering: chronological, thread-centric, no voting or ranking.
- Data model: flat global thread space with board tags rather than board-owned containers.
- Sync: git is canonical; HTTP text API is required for clients that cannot use git directly.

## 2. Canonical Repository Rules
- All canonical repository files are ASCII text with LF line endings.
- Canonical text files end with a trailing LF.
- Derived files may be regenerated from canonical files and are not part of the signed content model.
- One canonical payload file exists per post.
- Signed posts may also have a detached ASCII-armored signature file stored beside the payload file.

## 3. Record Types
- `post`: a user-visible thread root or reply.
- `moderation`: a signed moderation action such as hide, lock, pin, unpin, or ban.
- `identity-merge`: a signed record asserting that multiple keys belong to one logical identity.
- `tombstone`: a record indicating deletion or removal intent for a target record.

Version 1 requires only `post` for write APIs. Other record types may be introduced by direct repository operations first and exposed in APIs later.

## 4. Post Payload File Format

### 4.1 Storage form
- A post payload file is a plain text record with headers followed by a blank line followed by the body.
- Headers are contiguous at the top of the file.
- Header syntax is `Key: Value`.
- Header keys are case-insensitive for parsing.
- Header values are trimmed of leading and trailing whitespace during parsing.
- Unknown headers are allowed.
- The body may contain ASCII text, quoting, links, and a tiny markup subset.

### 4.2 Interoperable headers
For hand-written local content, headers may be omitted. For network-visible posts created by reference implementations, the following headers should be emitted:

- `Type: post`
- `Author: <fingerprint-or-anon-mode>`
- `Timestamp: <ISO-8601 UTC>`
- `Thread-ID: <root-record-id>` for replies
- `Parent-ID: <parent-record-id>` for replies
- `Board-Tags: <space-separated-tags>`
- `Subject: <single-line-subject>` for thread roots

### 4.3 Example post payload
```text
Type: post
Author: 0123456789abcdef0123456789abcdef01234567
Timestamp: 2026-03-13T15:00:00Z
Board-Tags: general meta
Subject: First thread

Hello world.
> quoted text
```

## 5. Canonicalization For IDs And Signatures

### 5.1 Purpose
Stored files may preserve flexible header ordering, but signing and cross-implementation comparison require one canonical byte sequence.

### 5.2 Canonical payload algorithm
To canonicalize a payload file:

1. Parse headers until the first blank line.
2. Lowercase all header keys for canonical processing.
3. Trim leading and trailing whitespace from header values.
4. Normalize the body to LF line endings and ensure a trailing LF.
5. Emit recognized headers in this fixed order when present:
   - `type`
   - `author`
   - `timestamp`
   - `thread-id`
   - `parent-id`
   - `board-tags`
   - `subject`
6. Emit any remaining headers in lowercase lexicographic key order.
7. For `board-tags`, split on ASCII whitespace, lowercase each tag, sort lexicographically, and join with a single space.
8. Separate headers from body with one blank line.

The resulting byte stream is the canonical payload.

### 5.3 Record identifiers
- `Record-ID` is the lowercase hexadecimal SHA-256 hash of the canonical payload bytes.
- `Thread-ID` is the `Record-ID` of the thread root post.
- Replies reference both `Thread-ID` and `Parent-ID`.

### 5.4 Detached signatures
- Signed posts use a detached ASCII-armored OpenPGP signature over the canonical payload bytes.
- The signature file path matches the payload file path with `.asc` appended.
- Unsigned posts are permitted only if local instance policy allows them.

## 6. Identity Model
- OpenPGP is used for key generation and detached signatures, not for higher-level identity semantics.
- A browser client may generate keys locally and store them in local storage for version 1.
- A first identity bootstrap may be done by publishing a post whose body contains the user's ASCII-armored public key.
- Display names are profile-layer data and can be handled in later records.
- Key rotation and multi-key identity grouping use signed `identity-merge` records that reference full fingerprints.
- Servers may trust moderator-signed identity merges according to local policy.

## 7. Deletion, Pins, And Ephemerality
- Public-instance soft deletion is represented first by a `tombstone` or moderation record that references the target `Record-ID`.
- A server may remove soft-deleted or expired content from its current branch after writing the tombstone.
- Sensitive-content hard purge is also allowed: implementations may delete payload files, related signatures, derived indexes, and repository history as part of rewrite or compaction operations.
- History rewrite and periodic repo compaction are allowed local maintenance operations.
- Visible state is defined by the current branch plus local policy, not by permanent retention of every historical payload.
- Implementations must tolerate missing referenced payloads after purge and treat them as unavailable or purged content rather than repository corruption.
- Thread rendering must remain stable when replies reference purged ancestors: the UI or API may emit a placeholder for the missing record, but must not fail the entire thread read.
- Pinned threads are represented by signed moderation records referencing `Thread-ID`.
- For version 1, pin and unpin authority should be limited to moderators or other instance-defined privileged actors.

## 8. Repository Layout Draft

### 8.1 Canonical directories
- `records/posts/aa/bb/<record-id>.txt`
- `records/posts/aa/bb/<record-id>.txt.asc`
- `records/moderation/aa/bb/<record-id>.txt`
- `records/identity/aa/bb/<record-id>.txt`
- `records/tombstones/aa/bb/<record-id>.txt`

The `aa/bb` prefix directories are the first four hexadecimal characters of `Record-ID` split into two levels to avoid huge flat directories.

### 8.2 Derived indexes
- `indexes/boards/<board-tag>.txt`
- `indexes/threads/<thread-id>.txt`
- `indexes/profiles/<identity-id>.txt`
- `indexes/moderation/log.txt`

Derived indexes are rebuildable from canonical records. They exist for fast reads and byte-identical output generation.

### 8.3 Non-canonical state
- `state/cache/`
- `state/work/`
- `logs/`

These directories are local implementation details and should not affect canonical visible forum state.

## 9. CGI Script Contract

### 9.1 Fixed script set for version 1
- `list_index`
- `get_thread`
- `get_post`
- `get_profile`
- `get_moderation_log`
- `create_thread`
- `create_reply`

Each script should be callable as a CGI endpoint and may also be callable directly from the command line for testing.

### 9.2 Execution assumptions
- Input repository path is supplied by configuration or environment.
- Scripts operate against the current checked-out repository state.
- Successful read operations over the same repository state must return byte-identical output across implementations.
- Error responses must follow the same structure, but byte-for-byte identity is required only for success responses.

## 10. HTTP API Envelope

### 10.1 Transport
- Content-Type: `text/plain; charset=us-ascii`
- For simplicity, API commands use `POST` even for reads.
- The human web UI may use normal `GET` pages separately.

### 10.2 Request envelope
Each API request body uses this top-level form:

```text
FORUM/1 <command>
Request-ID: <opaque-client-id>
Payload-Length: <decimal>
Signature-Length: <decimal>

<payload-bytes><signature-bytes>
```

Rules:
- `Payload-Length` may be `0`.
- `Signature-Length` may be `0`.
- `<payload-bytes>` are ASCII bytes interpreted according to the command.
- `<signature-bytes>` are ASCII-armored detached signature bytes when present.
- If `Signature-Length` is `0`, there is no signature block.

### 10.3 Response envelope
Each API success response body uses this form:

```text
FORUM/1 200 ok
Body-Length: <decimal>

<body-bytes>
```

Each API error response body uses this form:

```text
FORUM/1 <status-code> <status-text>
Error-Code: <machine-code>
Body-Length: <decimal>

<body-bytes>
```

`<body-bytes>` are ASCII text.

## 11. Command Payload Formats

### 11.1 `create_thread`
- Payload is the canonical post payload text for a thread root.
- `Thread-ID` must be omitted from the root payload.
- `Parent-ID` must be omitted from the root payload.
- Signature should verify against the canonical payload when instance policy requires signed posting.

Success body:
```text
Record-ID: <record-id>
Thread-ID: <thread-id>
Commit-ID: <commit-id>
Stored-Path: <repo-path>
```

### 11.2 `create_reply`
- Payload is the canonical post payload text for a reply.
- `Thread-ID` must point to an existing root post in visible state.
- `Parent-ID` must point to an existing visible post in the same thread.

Success body:
```text
Record-ID: <record-id>
Thread-ID: <thread-id>
Parent-ID: <parent-id>
Commit-ID: <commit-id>
Stored-Path: <repo-path>
```

### 11.3 `get_post`
Request payload body:
```text
Record-ID: <record-id>
```

Success body is the exact canonical payload bytes of the requested post when the payload remains available.

If the record is known but has been soft-deleted or purged, the implementation should return an error response with a machine-readable code such as `deleted` or `purged`.

### 11.4 `get_thread`
Request payload body:
```text
Thread-ID: <thread-id>
Include-Deleted: no
```

Success body:
```text
Thread-ID: <thread-id>
Record-Count: <decimal>
Record-Lengths: <space-separated-decimals>

<record-1-bytes><record-2-bytes>...
```

Records are returned in canonical chronological thread order.
If the root thread record is unavailable due to purge, the implementation should return an error response with machine-readable code `not_found`.
If one or more non-root referenced records are unavailable due to purge, the response should preserve thread order and include deterministic placeholders in place of missing payload bytes. The exact placeholder form remains to be fixed, but it must be specified once and shared by all compliant implementations.

### 11.5 `list_index`
Request payload body:
```text
Board-Tag: <tag-or-empty>
Limit: <decimal>
Before: <cursor-or-empty>
```

Success body:
```text
Entry-Count: <decimal>

<thread-id>\t<timestamp>\t<author>\t<board-tags>\t<subject>
...
```

### 11.6 `get_profile`
Request payload body:
```text
Identity-ID: <identity-id>
```

Success body is a deterministic plain-text profile summary derived from visible records.

### 11.7 `get_moderation_log`
Request payload body:
```text
Limit: <decimal>
Before: <cursor-or-empty>
```

Success body is a deterministic plain-text list of visible moderation records.

## 12. Byte-Identical Output Requirements
- Read command success responses must be byte-identical across compliant implementations for the same repository state and request payload.
- Determinism requires:
  - stable canonicalization
  - stable sort order
  - UTC ISO-8601 timestamps
  - LF line endings
  - explicit field separators
  - no locale-sensitive formatting
- Error responses should use the same top-level structure and machine-readable error codes, but exact body wording may differ.

## 13. Open Points To Confirm
- Whether version 1 should require signatures by default or allow unsigned posts by default.
- Whether `Record-ID` should hash the canonical payload exactly as stored or a stricter semantic subset.
- Whether the sibling `.asc` signature file approach is preferred over inline signature blocks inside payload files.
- Whether derived indexes should be committed, generated on demand, or allowed either way by instance policy.
- What exact placeholder form should represent purged non-root records in `get_thread` and related read APIs.
