## Stage 1 - browser signing shell and signature-aware backend helpers
- Changes:
  - Vendored the official OpenPGP.js browser module and added a browser-side signed-posting script for local key generation/import, canonical payload building, detached signing, and signed submission.
  - Added signed compose pages and navigation hooks in the existing web UI for thread and reply composition.
  - Added signature-aware backend helpers for detached-signature verification, sibling `.asc` storage planning, and dry-run signed submission results.
  - Added `/api/create_thread` and `/api/create_reply` POST routes in dry-run mode so the browser can submit signed payloads and receive deterministic preview responses without writing repository changes yet.
- Verification:
  - Confirmed `/compose/thread` renders successfully and serves the browser signing module.
  - Generated an OpenPGP keypair and detached signature through the vendored OpenPGP.js module in a local test harness, then confirmed `/api/create_thread` returns a `200 OK` dry-run preview with signature/public-key sidecar paths and a signer fingerprint.
  - Confirmed `/api/create_thread` returns a stable `400 Bad Request` error when signature material is omitted.
- Notes:
  - Stage 2 will switch signed thread creation from dry-run preview to real storage and git commits.
  - Stage 3 will do the same for signed replies.

## Stage 2 - signed thread creation from the browser
- Changes:
  - Switched the browser-facing `/api/create_thread` route from dry-run preview to real write behavior.
  - Switched the browser thread compose page from preview mode to real signed submission mode.
  - Reused the shared signed-posting service so successful browser thread submissions now write the payload file, detached signature file, and public-key sidecar in one git-backed commit.
- Verification:
  - Submitted a signed thread to `/api/create_thread` against a temporary local clone and confirmed a `200 OK` response with `Record-ID`, `Commit-ID`, `Signature-Path`, `Public-Key-Path`, and `Signer-Fingerprint`.
  - Confirmed the temporary clone contained `records/posts/stage2-browser-thread.txt`, `records/posts/stage2-browser-thread.txt.asc`, and `records/posts/stage2-browser-thread.txt.pub.asc`.
  - Confirmed the temporary clone created git commit subject `create_thread: stage2-browser-thread`.
  - Confirmed the new signed thread was immediately visible through `/api/get_thread?thread_id=stage2-browser-thread` and `/threads/stage2-browser-thread` when the reader was pointed at the temporary clone.
- Notes:
  - Signed reply creation remains in dry-run preview mode until Stage 3.
