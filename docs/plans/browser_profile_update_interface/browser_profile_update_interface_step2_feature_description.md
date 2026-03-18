## Problem
The forum can already accept signed `update_profile` submissions and render the current display name on profile and attribution surfaces, but a browser user still has no web interface for changing that name. The next slice should add the smallest useful frontend username-update flow so a user can update their current username/display name from the existing web app without pulling in full account settings, session auth, or a broader client rewrite.

## User Stories
- As a browser user, I want a web page where I can update my username/display name so that I do not need to craft signed profile-update requests manually.
- As a browser user with an existing local signing key, I want the web interface to reuse that key so that I can prove identity without leaving the app.
- As a reader, I want the updated username to appear on the profile page and other signed attribution surfaces so that identity presentation stays consistent.
- As a future implementer, I want the browser flow to stay aligned with the canonical `update_profile` contract so that frontend and API behavior do not drift apart.

## Core Requirements
- The slice must add one minimal browser UI for setting or replacing the current username/display name inside the existing web app.
- The slice must reuse the existing signed `update_profile` contract as the canonical write path rather than inventing a second profile-update format.
- The slice must keep the public profile view readable for all visitors while giving users a clear path into the dedicated update flow.
- The slice must show deterministic success or failure feedback after submission so users can tell whether their signed update was accepted.
- The slice must avoid session/auth work, broader account settings, avatars, bios, or a generic multi-action browser framework.

## Shared Component Inventory
- Existing web profile surface: extend `/profiles/<identity-slug>` as the main readback surface for the current username/display name and as the natural place to link into the update flow.
- Existing browser signing pattern: reuse the current compose-style browser signing experience so key generation/import, local key reuse, payload preview, and response display stay consistent with other signed write actions.
- Existing API write surface: reuse `/api/update_profile` as the canonical submission target because the backend contract already exists and should remain the single source of truth for profile updates.
- Existing read surfaces: keep `/api/get_profile`, profile pages, and signed attribution labels as the shared readback surfaces that confirm the new username is visible after a successful update.
- New web write surface: add one dedicated browser page for profile updates because the current web write pages only cover signed threads and replies.

## Simple User Flow
1. A browser user opens the dedicated username-update page from the existing web app.
2. The page shows the current username/display name context and prepares the user's local signing key.
3. The user enters a new username/display name and submits the signed update through the browser flow.
4. The server validates the signed request through the existing `update_profile` contract and returns a deterministic result.
5. The user sees the result in the web interface and can confirm the updated name on the profile page and other signed attribution surfaces.

## Success Criteria
- A browser user can update their username/display name through a dedicated page in the existing web app.
- The browser flow reuses the canonical signed profile-update contract instead of introducing a separate profile-write mechanism.
- After a successful submission, the updated name appears on `/profiles/<identity-slug>` and on other existing signed attribution surfaces.
- When the submission fails, the interface shows a clear deterministic error result and leaves existing read surfaces unchanged.
- The slice is narrow enough to deliver browser profile editing without adding full account-management scope.
