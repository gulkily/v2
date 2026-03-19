# My Profile Nav Stable Rendering Step 1: Solution Assessment

## Problem statement
Choose the smallest useful way to stop the primary navigation from shifting when the `My profile` link is revealed after page load, without turning the next slice into a broader authentication or account-navigation redesign.

## Option A — Render a stable `My profile` nav slot server-side and let the browser fill in only its target or count
- Pros:
  - Directly addresses the visible problem because the nav layout is stable before JavaScript runs.
  - Keeps the existing `My profile` affordance and current profile-led account flow intact.
  - Stays narrow by changing presentation and enhancement behavior rather than adding a new account model.
  - Still leaves room for client-side badge or count updates after load.
- Cons:
  - The server still cannot know the current browser-held identity, so the initial href or label may need to be a neutral placeholder.
  - Requires care so the pre-rendered slot is useful and not misleading for users without a stored key.

## Option B — Keep the current hidden-link model and reserve space with CSS or a placeholder shell
- Pros:
  - Smaller than changing the nav contract.
  - Preserves the current browser-only identity derivation logic in `profile_nav.js`.
  - Could reduce layout shift without deciding a stronger server-rendered fallback.
- Cons:
  - Solves the motion symptom more than the discoverability or polish problem.
  - Risks leaving an awkward empty gap or skeleton-like affordance in the primary nav.
  - Keeps the real `My profile` link absent until JavaScript enhancement finishes.

## Option C — Move `My profile` out of the primary nav into a later-loading account widget or page-local control
- Pros:
  - Avoids primary-nav layout shift by removing the late-added item from the main nav row.
  - Could isolate browser-derived identity affordances into a more explicitly client-side area.
- Cons:
  - Weakens the original product goal of having one persistent signed-user navigation entry point.
  - Pushes a focused polish fix into a broader information-architecture change.
  - Risks making profile access less obvious rather than more stable.

## Recommendation
Recommend Option A: render a stable `My profile` nav slot server-side and let the browser fill in only its target or count.

This is the smallest coherent slice because the current problem is not that the product chose the wrong destination; it is that the destination appears too late and shifts the shared nav. The next slice should preserve the existing `My profile` entry point, keep browser-derived identity resolution where needed, and make the shared header stable before JavaScript enhancement runs.
