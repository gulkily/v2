## Problem
Browser-stored private key material is currently shown on public profile pages, which blurs the boundary between public identity viewing and private local account state. The next slice should move key viewing to a dedicated account/key page so private key management has one clear, non-public destination.

## User Stories
- As a signed user, I want one dedicated page for my browser-stored key material so that private key viewing feels personal and intentional.
- As a visitor viewing profiles, I want profile pages to stay public-facing so that I do not see private-key UI that does not belong to that profile.
- As a returning user, I want key material to appear in a consistent place across account-related flows so that I know where to go when I need it.
- As a maintainer, I want one canonical key-management surface so that key-related UI does not drift across unrelated pages.

## Core Requirements
- Public profile pages must no longer render browser-stored private-key or public-key viewers.
- The product must provide one dedicated account/key page for viewing browser-stored key material on the current device.
- The dedicated page must clearly remain a local browser/account surface rather than a public profile surface.
- Existing account-related flows that already expose browser key material must continue to point users toward the same canonical key-management destination instead of creating more variants.
- The change must stay within existing identity and browser-storage concepts; no new account model or server-stored private-key behavior is introduced.

## Shared Component Inventory
- Existing public profile surface `/profiles/<identity-slug>`: extend by removing key material from this public page; it should remain profile-focused, not key-management-focused.
- Existing compose surface(s): reuse the current key-material presentation as the visual/content baseline because compose already teaches users that keys are local browser state.
- Existing profile update surface `/profiles/<identity-slug>/update`: extend to direct users toward the canonical account/key page rather than acting as a second long-term home for key viewing.
- Existing merge request action surface: extend to rely on the same canonical key-management destination for browser key material rather than becoming a competing key page.
- Existing browser key storage and signing assets: reuse as the canonical local data source because this feature is about where key material is shown, not how it is stored.
- New dedicated account/key page: add as the single canonical surface for browser-stored key viewing because none of the existing public or task-specific pages is the right permanent home.

## Simple User Flow
1. A signed user wants to inspect the browser-stored key material for the current device.
2. The user opens the dedicated account/key page.
3. The page shows the locally available private/public key material and related status messaging.
4. The user returns to profile, compose, or other account tasks without seeing the same key viewer embedded on public profile pages.

## Success Criteria
- Public profile pages no longer show browser-stored key material.
- There is exactly one clear account/key destination for viewing browser-stored key material.
- The dedicated page communicates local browser ownership clearly enough that it is not confused with a public identity page.
- Existing account-related flows continue to work without creating multiple competing homes for the same key viewer.
