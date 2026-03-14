## Stage 1 - CGI command shell and shared helpers
- Changes:
  - Added a small `forum_cgi` helper package for write-command parsing, validation, storage-path selection, commit preparation, and plain-text CGI response rendering.
  - Added separate `cgi-bin/create_thread.py` and `cgi-bin/create_reply.py` entrypoints.
  - Refactored canonical post parsing so both read and write paths can parse the same payload text directly.
  - Kept both write commands in dry-run mode for this stage so the shell and shared helpers are proven without creating repository changes yet.
- Verification:
  - Called `cgi-bin/create_thread.py` with a valid root payload and confirmed a `200 OK` dry-run preview showing the future record ID, storage path, and commit message.
  - Called `cgi-bin/create_reply.py` with a valid reply payload targeting `root-002` and confirmed a `200 OK` dry-run preview including `Parent-ID`.
  - Called `cgi-bin/create_thread.py` with an empty request body and confirmed a stable `400 Bad Request` CGI response.
- Notes:
  - Stage 2 will switch `create_thread` from dry-run preview to real file creation and git commit behavior.
  - Stage 3 will do the same for `create_reply`.

## Stage 2 - create_thread
- Changes:
  - Switched `cgi-bin/create_thread.py` from dry-run preview to real write behavior.
  - Added shared storage-and-commit handling so an accepted root payload now writes `records/posts/<post-id>.txt` and creates a deterministic git commit.
  - Kept `create_reply` in dry-run mode so the loop still advances one write command at a time.
- Verification:
  - Ran `cgi-bin/create_thread.py` against a temporary local clone and confirmed a `200 OK` response with `Record-ID`, `Thread-ID`, `Commit-ID`, and `Stored-Path`.
  - Confirmed the command created `records/posts/stage2-created-thread.txt` in the temporary clone and produced git commit subject `create_thread: stage2-created-thread`.
  - Confirmed the new thread was immediately visible through `/api/get_thread?thread_id=stage2-created-thread` and `/threads/stage2-created-thread` when the existing reader was pointed at the temporary clone.
- Notes:
  - Success responses now return `Record-ID`, `Thread-ID`, `Commit-ID`, and `Stored-Path`, matching the Loop 4 write contract for thread creation.

## Stage 3 - create_reply
- Changes:
  - Switched `cgi-bin/create_reply.py` from dry-run preview to real write behavior.
  - Reused the shared validation, storage, and commit helpers so replies now produce canonical post files and deterministic git commits.
  - Preserved stable error handling for missing thread targets, missing parent targets, and invalid cross-thread parent references.
- Verification:
  - Ran `cgi-bin/create_reply.py` against a temporary local clone and confirmed a `200 OK` response with `Record-ID`, `Thread-ID`, `Parent-ID`, `Commit-ID`, and `Stored-Path`.
  - Confirmed the command created `records/posts/stage3-created-reply.txt` in the temporary clone and produced git commit subject `create_reply: stage3-created-reply`.
  - Confirmed the new reply was immediately visible through `/api/get_thread?thread_id=root-002` and `/posts/stage3-created-reply` when the existing reader was pointed at the temporary clone.
  - Called `cgi-bin/create_reply.py` with an unknown thread target and confirmed a stable `404 Not Found` CGI response with `Error-Code: not_found`.
- Notes:
  - Success responses now return `Record-ID`, `Thread-ID`, `Parent-ID`, `Commit-ID`, and `Stored-Path`, matching the Loop 4 write contract for reply creation.
