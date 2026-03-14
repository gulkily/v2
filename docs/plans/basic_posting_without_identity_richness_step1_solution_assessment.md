## Problem Statement
Choose the smallest useful way to add posting for new threads and replies without turning this loop into identity, signing, moderation, or backend-runtime work.

### Option A: Add minimal write endpoints inside the existing WSGI app
- Pros:
  - Fastest path to a demonstrable write loop for both humans and agents.
  - Reuses the canonical post parsing rules and the read surfaces already in place.
  - Lets the project prove the full repository cycle: validate payload, write text file, commit to git, and immediately show the result in the UI and API.
  - Keeps the protocol surface visible now while deferring the final CGI-style split to a later loop.
- Cons:
  - The first write path is Python-hosted, so later extraction into parallel implementations will still be needed.
  - Needs careful boundaries so validation, file-writing rules, and commit behavior do not get tangled with request routing.
  - Direct commits introduce single-writer assumptions that may need refinement later.

### Option B: Implement `create_thread` and `create_reply` as separate CGI-style scripts now
- Pros:
  - Aligns earlier with the long-term multi-language backend model.
  - Makes the write contract explicit from the start.
  - Could reduce later extraction work if the CGI contract remains the final execution shape.
- Cons:
  - Expands this loop significantly.
  - Pulls runtime, dispatch, and script boundary decisions into the first write feature before the core write semantics are proven.
  - Slows down the first end-to-end posting demo.

### Option C: Add a local import helper or file-drop workflow instead of HTTP posting
- Pros:
  - Simplest implementation path for validation and file creation.
  - Useful for fixtures and operator tooling.
  - Could still prove canonical post acceptance rules.
- Cons:
  - Does not satisfy the checklist goal of actual posting behavior through the application surface.
  - Gives agents and browser clients no real write contract.
  - Delays the point where newly created content appears immediately in the existing UI and API.

## Recommendation
Selected direction: Option B, implement `create_thread` and `create_reply` as separate CGI-style scripts now.

This makes Loop 4 larger, but it aligns the first write path with the stated long-term architecture instead of treating multi-language execution as a later extraction step. To keep that from sprawling, the loop should stay strict about boundaries:

- The write surface should still be limited to `create_thread` and `create_reply`.
- Request bodies should be plain ASCII canonical post payloads.
- Validation, canonical file writing, and success/error serialization should be shared contract helpers, not embedded ad hoc in each script.
- The CGI boundary should be treated as language-neutral so a Python implementation can be followed by a Perl implementation against the same fixtures.
- Accepted posts should still be written directly to `records/posts/` and committed immediately with deterministic commit messages.
- Signing, identity richness, moderation, and broader sync/federation behavior should remain out of scope for this loop.

That gives the project an end-to-end posting demo while also forcing the command contract, payload rules, and script interfaces to become explicit early. The tradeoff is more up-front structure now in exchange for less architectural reshaping later.
