## Problem
Eligible signed users already have a shared `Account setup` banner surface in the page shell, but the banner only becomes visible after browser-side JavaScript reads local key state and calls a follow-up API. That delay makes the canonical account-setup prompt disappear from the initial HTML even on pages where the user should see it immediately.

## User Stories
- As an eligible signed user, I want the `Account setup` module to be present in the initial page HTML so that the next account action is visible immediately on first render.
- As an eligible signed user, I want the banner to keep linking to the existing username-update flow so that account setup uses the same destination the product already established.
- As an ineligible or unsigned visitor, I want the shared page shell to avoid showing a misleading account-setup prompt so that the banner only appears when it is actionable.
- As a maintainer, I want this fix to extend the existing shared banner surface instead of introducing a new onboarding area so that account setup stays canonical and narrow in scope.

## Core Requirements
- The shared `Account setup` module must render as part of initial server HTML for users who are currently eligible to claim a username.
- The feature must preserve the existing shared banner placement and copy rather than moving account setup into a different page region or separate hub.
- The visible CTA must continue to send eligible users to the existing username-update route for their identity.
- The browser must provide request-time identity context through a server-signed fingerprint hint cookie so shared server rendering can evaluate eligibility on normal page requests.
- The hint cookie must be treated only as a personalization/input hint for rendering and routing decisions like the account-setup banner, not as authentication or authorization.
- Users who are not eligible, or whose hint cookie is missing, stale, or invalid, must not receive a misleading visible banner on first render.
- Client-side code may still enhance or refresh the banner after load, but JavaScript must no longer be the first mechanism that makes the module appear for the happy path.

## Shared Component Inventory
- Existing shared page banner in `render_page(...)` and `render_username_claim_cta_html()`: extend this canonical surface because it already defines the shared `Account setup` module and placement used across page renders.
- Existing browser-held public key in local storage plus identity derivation in `profile_nav.js`: extend this path so the browser can tell the server which fingerprint to hint, while keeping the browser key itself local.
- New server-signed identity-hint cookie contract: add this shared request-time identity input so server-rendered pages can personalize the banner without introducing a full auth/session system.
- Existing username-claim CTA asset `username_claim_cta.js`: keep as an enhancement path for post-load refresh behavior, but stop relying on it as the primary visibility mechanism for initially eligible users.
- Existing username-claim API `/api/get_username_claim_cta`: preserve as an existing account-status contract where it still helps client refreshes, but do not require it for the first visible render of the banner.
- Existing username update page `/profiles/<identity-slug>/update`: reuse unchanged as the canonical account-setup destination instead of creating a new setup route.

## Simple User Flow
1. A signed user visits a page that includes the shared page shell.
2. The browser derives the current fingerprint from its local key and keeps the server-signed identity-hint cookie current.
3. On the next page request, the server validates the hint cookie and resolves whether that fingerprint is eligible for the username-claim account-setup action.
4. If eligible, the initial HTML includes the visible `Account setup` banner with the correct username-update destination.
5. If not eligible, or if the hint cookie is absent or invalid, the shared page shell renders without a visible account-setup prompt.
6. After load, client-side code may refresh or clear the banner state if browser context changes, without being responsible for the first reveal in the normal eligible case.

## Success Criteria
- On eligible requests, the initial HTML response already contains the visible `Account setup` module and actionable link.
- The banner keeps its current shared placement and still routes to the existing username-update flow.
- Invalid, missing, or stale identity-hint cookies do not produce a false-positive account-setup banner.
- The server-side hint mechanism does not become the source of truth for privileged account actions beyond rendering/navigation hints.
- The change does not create a separate onboarding page, duplicate CTA surface, or alternate account-setup destination.
