## Problem
The forum can now create signed posts from the browser, but it still has no coherent way to turn those keys and signatures into a visible identity surface. The next slice should add the smallest useful identity bootstrap and profile read model so a user can make a first signed post, have their public key published automatically if no bootstrap exists yet, acquire a stable `Identity-ID`, and be viewed through deterministic profile reads without pulling in full profile editing, key rotation, or richer trust semantics.

## User Stories
- As a browser user, I want my first signed post to bootstrap identity automatically so that I do not need to manage a separate registration step.
- As a reader, I want to view a stable profile summary derived from visible records so that signed authorship is understandable to humans and agents.
- As a future backend implementer, I want identity bootstrap and `get_profile` behavior to be explicit and deterministic so later implementations can reproduce the same results.
- As a reviewer, I want the first identity slice to reuse existing signed-post infrastructure instead of inventing a second storage or transport model.

## Core Requirements
- The slice must define a minimal public-key bootstrap post shape using the existing canonical post format.
- The slice must publish the user's public key automatically on the first signed post when no visible bootstrap exists yet for that key.
- The slice must treat the bootstrap material as the first visible anchor for an identity and derive a stable `Identity-ID` from the published key material.
- The slice must add deterministic profile summary derivation from visible repository records associated with that identity.
- The slice must expose that derived profile through both a plain-text `get_profile` read surface and a simple web profile view.
- The slice must reuse the existing detached-signature model and signed posting flow rather than adding a separate registration transport.
- The slice must avoid prompting for usernames or display names, as well as profile editing, key rotation, multi-key merge handling, moderator-trusted merge assertions, moderation policy, or richer anonymous-identity behavior.

## Shared Component Inventory
- Existing UI surfaces: extend the current web app with first-post bootstrap behavior and a read-only user/profile page, without adding a separate registration form.
- Existing API surfaces: add `get_profile` to the plain-text read API and keep its response deterministic across implementations.
- Existing data surfaces: reuse canonical post files and detached signature sidecars; the bootstrap material is stored through the same repository-backed posting flow as the user's first signed post.
- Existing backend surfaces: build on the current posting and signing helpers so key publication, signature verification, and read-model derivation all operate from the same repository-backed data.

## Simple User Flow
1. A browser user submits their first signed post through the existing posting flow.
2. If no visible bootstrap exists yet for that key, the system automatically publishes the user's public key as bootstrap material alongside that first signed post.
3. The server stores the canonical post and detached signature using the existing posting path.
4. The system derives a stable `Identity-ID` from the visible bootstrap key material and associates later visible signed posts from that key with the same identity.
5. A client requests `get_profile` or visits the user/profile page for that `Identity-ID`.
6. The server returns a deterministic profile summary derived from visible records, including the bootstrap anchor and current visible activity for that identity.

## Success Criteria
- A user's first signed post automatically bootstraps identity when no visible bootstrap exists yet for that key.
- The system derives a stable `Identity-ID` from the bootstrap key material without requiring a separate registration record type.
- A client can retrieve a deterministic plain-text profile summary through `get_profile`.
- A human reader can open a simple user/profile page that reflects the same identity summary as the API.
- The identity/profile behavior is specific enough to serve as a fixture target for later non-Python implementations.
- The user is not required to provide a username or display name in this slice.
