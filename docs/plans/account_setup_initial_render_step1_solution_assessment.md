# Account Setup Initial Render Step 1: Solution Assessment

## Problem statement
Choose the smallest reliable way to make the shared `Account setup` module appear in the initial page HTML for eligible users instead of showing up only after browser-side JavaScript runs.

## Option A — Render the eligibility-aware account-setup module on the server
- Pros:
  - Matches the requirement directly because the module is present at first paint.
  - Keeps the current shared page-level placement instead of inventing a new surface.
  - Removes the slow-connection delay caused by waiting on browser storage and a follow-up API call before reveal.
  - Preserves a clean path for later progressive enhancement if client-side refresh behavior is still useful.
- Cons:
  - Requires the server-rendered page flow to know enough account state to decide eligibility.
  - Tightens the contract between shared page rendering and account-status resolution.

## Option B — Keep browser-side eligibility, but pre-render a generic placeholder and fill it in later
- Pros:
  - Smaller backend change because the current eligibility lookup can stay mostly client-driven.
  - Improves perceived layout stability because space for the module exists immediately.
- Cons:
  - Does not satisfy the requirement that the module itself appear immediately in final page content.
  - Still depends on JavaScript to decide whether the user actually gets the account-setup action.
  - Risks showing vague or dead-end content during the delay window.

## Option C — Move the account-setup prompt into existing always-visible page chrome
- Pros:
  - Avoids late insertion by relying on markup that already ships with the page shell.
  - Could reduce visual complexity if the product prefers a lighter prompt.
- Cons:
  - Changes the UX shape instead of fixing the current module behavior.
  - Weakens the dedicated account-setup callout that the current design already established.
  - Still needs an eligibility strategy, so it does not remove the core decision problem.

## Recommendation
Recommend Option A: render the eligibility-aware account-setup module on the server.

This is the smallest coherent fix because it solves the actual failure mode rather than masking it. The next step should treat the account-setup CTA as part of canonical page rendering for eligible users, with JavaScript limited to enhancement rather than first visibility.
