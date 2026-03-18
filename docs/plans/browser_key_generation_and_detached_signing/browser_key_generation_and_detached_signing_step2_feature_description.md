## Problem
The forum can now accept new threads and replies through CGI-style write commands, but the frontend still cannot post and the system does not yet handle detached signatures. The next slice should add the smallest useful browser-side signing and posting flow so a user can generate or import an OpenPGP key, sign a canonical payload in the browser, submit it, and immediately read the signed post back through the existing UI and API.

## User Stories
- As a browser user, I want to generate or import an OpenPGP key locally so that I can post without leaving the web interface.
- As a browser user, I want the post I submit to be signed client-side with a detached signature over canonical post bytes.
- As a server operator, I want the backend to verify and store detached signatures in a deterministic way so that signed posts remain auditable in git-backed storage.
- As a future backend implementer, I want the signature-aware posting contract to stay explicit and language-neutral so later implementations can reproduce the same success and error behavior.

## Core Requirements
- The slice must add a minimal browser posting surface for new threads and replies inside the existing web app.
- The slice must allow a browser user to generate a new OpenPGP key locally or import an existing ASCII-armored private key.
- The slice must sign a canonical normalized post payload client-side and submit a detached ASCII-armored signature alongside the payload.
- The slice must extend the posting backend only as much as needed to accept, verify when policy requires it, and store detached signature files beside canonical payload files.
- The slice must keep success and error responses deterministic enough for later multi-language implementations to match.
- The slice must avoid full identity bootstrap flows, profile editing, moderation signing, key rotation flows, or richer anonymous-mode policy.

## Shared Component Inventory
- Existing UI surfaces: extend the current web app with a small posting-oriented browser UI; the existing thread and post views remain the readback surface after a successful signed post.
- Existing API surfaces: reuse the current CGI-style write contract for `create_thread` and `create_reply`, with the smallest signature-aware extension needed for detached signature submission and verification.
- Existing data surfaces: reuse `records/posts/` for canonical payload files and add sibling detached `.asc` files for signed posts, aligned with the protocol draft.
- Existing backend surfaces: build on the Loop 4 write helpers so payload parsing, validation, storage, and git commits remain shared between signed and unsigned posting paths.

## Simple User Flow
1. A browser user opens the posting UI and generates or imports an OpenPGP key locally.
2. The user composes a new thread or reply in the browser.
3. The browser canonicalizes the payload, signs it client-side, and submits the payload plus detached signature through the posting contract.
4. The server validates the payload, verifies the signature when policy requires it, stores the canonical payload and sibling `.asc` file, and creates a git commit.
5. The new signed content is immediately visible through the existing web UI and read-only API.

## Success Criteria
- A browser user can generate or import a local OpenPGP key and use it to submit a signed thread.
- A browser user can submit a signed reply to an existing thread.
- Accepted signed posts produce both canonical payload files and detached signature files in repository storage.
- Signed posts are visible through the existing thread pages and read-only plain-text API after submission.
- Signature-aware success and error responses are stable enough to serve as fixtures for later non-Python implementations.
