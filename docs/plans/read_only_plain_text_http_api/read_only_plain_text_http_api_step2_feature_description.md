## Problem
The forum is now readable through the web UI, but agents and CLI users still lack a simple read-only HTTP interface over the same canonical repository state. The next slice should expose that read surface in plain text without adding write behavior or prematurely locking in the final multi-language execution model.

## User Stories
- As an agent, I want a plain-text read API so that I can fetch index, thread, and post data without scraping HTML.
- As a CLI user, I want stable text responses so that I can inspect forum state with ordinary shell tools.
- As a future backend implementer, I want the read contract to be language-neutral so that Perl, Python, and later implementations can reproduce the same success output.
- As a human operator, I want the API to reuse the same repository truth as the web renderer so that browser and API views stay aligned.

## Core Requirements
- The slice must expose read-only plain-text HTTP endpoints for at least `list_index`, `get_thread`, and `get_post`.
- The slice must serve data derived directly from the canonical post files already used by the web renderer.
- The slice must define deterministic plain-text response shapes suitable for later multi-language implementations to match.
- The slice must avoid introducing write endpoints, signing flows, moderation actions, or durable derived index policy.

## Shared Component Inventory
- Existing UI surfaces: reuse the current read-only web renderer as the human-facing view over the same repository state.
- Existing API surfaces: none; this slice creates the first canonical machine-facing read interface.
- Existing data surfaces: reuse `records/posts/` and `docs/specs/canonical_post_record_v1.md` as the source of truth for API responses.
- Existing backend surfaces: reuse or extend the current read logic so browser and API views are driven by the same canonical parsing and grouping behavior.

## Simple User Flow
1. A client sends a read-only HTTP request for the index, a thread, or an individual post.
2. The server reads the canonical post files from the repository.
3. The server returns a deterministic plain-text response for that request.
4. The client compares or consumes the response alongside the existing web view of the same data.

## Success Criteria
- A CLI or agent can retrieve an index, a thread, and an individual post through plain-text HTTP responses.
- The API responses describe the same repository state currently shown in the browser UI.
- The response shapes are simple and deterministic enough to serve as fixtures for later non-Python implementations.
- The loop adds no write-path behavior or other scope outside read-only API access.
