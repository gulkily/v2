## Stage 1
- Goal: establish the CGI-style write command shell and shared posting helpers.
- Dependencies: approved Step 2; existing canonical post spec, repository layout, and read surfaces.
- Expected changes: add the minimal command entrypoint structure for write operations, define shared helpers for parsing ASCII request bodies, validating canonical post payloads, serializing deterministic success/error responses, choosing storage paths, and preparing git commit operations; no signing, moderation, or profile logic.
- Verification approach: run the command shell locally with a sample payload and confirm it returns stable plain-text validation errors or shell-level success output without needing browser forms.
- Risks or open questions:
  - letting Python-specific command wiring leak into what should be a language-neutral contract
  - coupling storage, validation, and commit logic too tightly for later Perl parity work
- Canonical components/API contracts touched: `create_thread` and `create_reply` command envelope; canonical post payload acceptance rules; plain-text write response shapes.

## Stage 2
- Goal: implement `create_thread` end to end through the CGI-style write contract.
- Dependencies: Stage 1.
- Expected changes: add the first real write command for new thread roots, enforce root-payload rules such as omitted `Thread-ID` and `Parent-ID`, write accepted root posts into `records/posts/`, and create deterministic git commits with stable success output; planned helpers such as `validate_thread_payload(text) -> PostDraft` and `store_post(draft) -> StoredPost`.
- Verification approach: submit a valid root payload, confirm a new canonical post file appears in `records/posts/`, confirm a git commit is created, and confirm the new thread becomes visible through the existing UI and read-only API.
- Risks or open questions:
  - deciding how strictly filename selection follows `Post-ID`
  - keeping commit messages deterministic without overcommitting to long-term policy too early
- Canonical components/API contracts touched: `create_thread`; canonical root-post validation; deterministic storage and success response behavior.

## Stage 3
- Goal: implement `create_reply` end to end through the CGI-style write contract.
- Dependencies: Stage 2.
- Expected changes: add reply creation, enforce that `Thread-ID` points to an existing root and `Parent-ID` points to an existing post in the same thread, write accepted replies into `records/posts/`, create deterministic git commits, and return stable plain-text success and error responses; planned helpers such as `lookup_thread_for_write(thread_id) -> Thread | None` and `validate_reply_target(parent_id, thread_id) -> bool`.
- Verification approach: submit a valid reply payload to an existing thread, confirm the canonical post file and git commit are created, confirm the reply appears in the thread page and `get_thread`, and confirm invalid targets return stable plain-text errors.
- Risks or open questions:
  - write-time race conditions if multiple posts are created concurrently
  - reply validation rules may later need expansion for deleted or purged posts
- Canonical components/API contracts touched: `create_reply`; reply-target validation; deterministic write success/error behavior and git-backed persistence.
