## Problem
The browser compose flow currently rejects non-ASCII text even though users may naturally type smart quotes, em dashes, ellipses, emojis, or similar characters while drafting a message. The next slice should automatically correct clearly mappable non-ASCII characters before signing, while giving the user one fast way to remove unsupported characters that cannot be corrected safely.

## User Stories
- As a browser user, I want my composed message to be corrected automatically when I paste or type common non-ASCII punctuation so that I do not have to clean it up by hand before posting.
- As a browser user, I want the corrected text to match what is actually signed and submitted so that the payload preview and stored post are predictable.
- As a browser user, I want one explicit way to remove unsupported characters like emojis so that I can submit immediately without manually hunting them down.
- As a maintainer, I want the correction behavior to stay narrow and deterministic so that the compose flow improves without becoming a general rewrite or translation feature.
- As an operator, I want the backend ASCII-only contract to remain intact so that existing verification, storage, and repository behavior do not change.

## Core Requirements
- The slice must correct clearly mappable non-ASCII compose input in the browser before canonical payload signing happens.
- The slice must offer one explicit browser action to remove unsupported non-ASCII characters that remain after deterministic correction.
- The slice must keep the corrected text aligned across the visible compose form, payload preview, detached signature input, and submitted payload.
- The slice must preserve the existing backend contract that payload, signature, and stored record content are ASCII-only.
- The slice must apply consistently across existing browser-signed compose surfaces that derive canonical post payloads.
- The slice must avoid broader rewriting, translation, language normalization, or server-side mutation of already signed payloads.

## Shared Component Inventory
- Existing browser compose surface: extend the current browser signing flow in [`templates/assets/browser_signing.js`](/home/wsl/v2/templates/assets/browser_signing.js) because it already derives the canonical payload and enforces ASCII before signing.
- Existing compose pages: reuse the current thread, reply, and task compose pages rendered from [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py) and [`templates/compose.html`](/home/wsl/v2/templates/compose.html); no new page is needed.
- Existing profile-update signing surface: do not include [`templates/profile_update.html`](/home/wsl/v2/templates/profile_update.html) unless the same correction rule clearly applies to its user-entered text, because this feature is about composed message content first.
- Existing backend/API surfaces: reuse the current `/api/create_thread` and `/api/create_reply` submission contract unchanged because correction must happen before signing, not during submission.

## Simple User Flow
1. A user opens an existing browser compose page and types or pastes a message containing common non-ASCII characters.
2. The browser corrects those characters into deterministic ASCII equivalents before building the canonical payload.
3. If unsupported characters such as emojis remain, the compose UI offers one explicit action to remove them from the composed message.
4. The compose UI shows the final corrected result through the normal payload preview and signing flow.
5. The browser signs and submits the corrected ASCII payload through the existing write endpoint.
6. The stored post and readback view match the corrected text the user saw before submission.

## Success Criteria
- A browser user can compose and submit a thread or reply containing common non-ASCII punctuation without hitting the current ASCII rejection path.
- A browser user who includes unsupported characters such as emojis can remove them with one explicit action and continue to submission without manual per-character cleanup.
- The text shown in the compose form and payload preview after correction matches the text that is signed and stored.
- Existing backend create-thread and create-reply behavior remains unchanged apart from receiving already corrected ASCII payloads.
- The correction scope stays narrow enough that unsupported characters still surface clear errors instead of silent broad rewriting.
