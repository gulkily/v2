## Problem
Most self-service account controls already exist on the signed user’s profile page or on profile-linked sub-pages, but there is no obvious always-available way for a signed user to get back to that profile. The next slice should add the smallest useful “My profile” access path without creating a second account surface or reorganizing the existing profile, username-update, and merge-request flows.

## User Stories
- As a signed user, I want an obvious way to open my own profile so that I can quickly reach my account controls.
- As a signed user, I want the same profile entry point to lead me to username-change and merge-request actions so that account tasks stay easy to find.
- As a returning user, I want profile access to be predictable across pages so that I do not need to remember a direct profile URL.
- As a reader of the codebase, I want the feature to reuse the existing profile-led account surfaces so that navigation stays simple and canonical.

## Core Requirements
- The slice must add one clear signed-user affordance for opening the current user’s profile page.
- The affordance must resolve to the same canonical profile route the existing product already uses for profile reads.
- The slice must preserve the existing profile-led paths for username updates and merge management rather than duplicating those controls elsewhere.
- The slice must work consistently enough that a signed user can reach their profile from the main browsing flow without knowing their slug in advance.
- The slice must avoid a separate account hub, duplicated settings page, or broader site-navigation redesign.

## Shared Component Inventory
- Existing web profile surface `/profiles/<identity-slug>`: reuse as the canonical signed-user home because it already anchors self-service profile controls.
- Existing web profile-update surface `/profiles/<identity-slug>/update`: reuse unchanged as the username-change flow, reached from the profile page after the user gets there.
- Existing web merge-management surface `/profiles/<identity-slug>/merge`: reuse unchanged as the merge-request workflow, reached from the profile page after the user gets there.
- Existing shared site navigation or header surface: extend this canonical global affordance with one signed-user `My profile` entry point instead of creating a new account page.
- Existing browser signing and identity-resolution behavior: reuse as-is because this slice is about access and navigation, not new signing flows or identity semantics.

## Simple User Flow
1. A signed user browses any normal page in the app.
2. The UI shows a clear `My profile` entry point in the main signed-user navigation.
3. The user selects that entry point and lands on their canonical profile page.
4. From that profile page, the user can use the existing controls or links to update their username or manage merge requests.

## Success Criteria
- A signed user can reliably reach their own profile page from the primary signed-user navigation without manually entering a profile URL.
- The navigation target resolves to the same canonical profile route already used elsewhere in the product.
- Username-change and merge-request actions remain on the existing profile-led paths instead of being duplicated on a new account surface.
- The feature stays narrow enough that no separate account hub or broader navigation rewrite is required.
