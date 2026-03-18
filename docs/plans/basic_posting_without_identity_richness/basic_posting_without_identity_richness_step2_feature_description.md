## Problem
The forum is now readable through both the web UI and the plain-text read API, but it still cannot accept new content. The next slice should prove the first write path using CGI-style command scripts so that new threads and replies can be created from canonical ASCII payloads and immediately appear in the existing read surfaces.

## User Stories
- As a local operator or agent, I want to submit a new thread or reply through a simple write contract so that I can add content without editing repository files by hand.
- As a future backend implementer, I want the first write path to use explicit CGI-style command boundaries so that later Perl, Python, and other implementations can target the same contract.
- As a reviewer, I want accepted writes to produce canonical post files and git commits so that the repository remains the source of truth.
- As a human reader, I want newly created content to appear in the existing web UI and read API right after it is accepted.

## Core Requirements
- The slice must expose write behavior for `create_thread` and `create_reply` as separate CGI-style command scripts.
- The slice must accept plain ASCII canonical post payloads only.
- The slice must validate required headers and thread/reply relationships before writing any new record.
- The slice must write accepted posts directly into `records/posts/` using deterministic storage rules and create a git commit for each accepted write.
- The slice must define stable success and error response shapes that later implementations can reproduce.
- The slice must avoid browser-side key management, detached signatures, moderation actions, anonymous-mode policy, or richer identity/profile behavior.

## Shared Component Inventory
- Existing UI surfaces: reuse the current read-only web renderer as the human-facing readback after a successful post; this slice does not need to add browser posting forms.
- Existing API surfaces: reuse the current read-only plain-text API for verification after writes, while adding the first write-side CGI commands.
- Existing data surfaces: reuse `records/posts/` and `docs/specs/canonical_post_record_v1.md` as the canonical storage format for newly accepted content.
- Existing backend surfaces: build the write path as explicit CGI-style command entrypoints with shared helpers for validation, storage, and response serialization.

## Simple User Flow
1. A client sends a `create_thread` or `create_reply` request containing a canonical ASCII post payload.
2. The matching CGI-style command validates the payload and confirms the thread/reply relationship is allowed by current repository state.
3. If valid, the command writes the new canonical post file into `records/posts/` and creates a deterministic git commit.
4. The client receives a stable plain-text success response.
5. The new content is immediately visible through the existing thread pages and read-only API endpoints.

## Success Criteria
- A client can create a new thread through `create_thread` without editing repository files manually.
- A client can create a reply through `create_reply` when the referenced thread and parent post exist.
- Accepted writes produce canonical post files and git commits in the repository.
- Newly created content is visible through the existing web UI and read-only plain-text API.
- The write response and error shapes are deterministic enough to serve as fixtures for later non-Python implementations.
