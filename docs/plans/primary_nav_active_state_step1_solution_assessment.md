# Primary Nav Active State Step 1: Solution Assessment

## Problem statement
Choose the smallest useful way to make the shared primary nav clearly show the current page or section, including keeping `Activity` selected across its filtered subsections.

## Option A — Add a shared server-rendered active-nav contract and have the primary nav mark the matching section active
- Pros:
  - Matches the request directly because the shared navbar itself shows the current page.
  - Works on first render for both Python and PHP-served pages instead of waiting for client-side enhancement.
  - Fits the existing activity model because `/activity/` already treats `view=all|content|moderation|code` as subsections of one parent section.
  - Keeps the behavior consistent across all pages that reuse the shared header.
- Cons:
  - Requires the shared header render path to accept and preserve a current-section value.
  - Needs one clear rule for mapping detailed routes back to a top-level nav section.

## Option B — Add client-side navbar highlighting based on the current URL
- Pros:
  - Avoids threading active-section state through server render paths.
  - Could use one enhancement script across Python and PHP output.
  - Keeps the HTML contract smaller at first.
- Cons:
  - The active state would appear late instead of being correct in the initial HTML.
  - Duplicates route-parsing logic in the browser instead of using the server’s existing routing knowledge.
  - Weakens the static and no-JavaScript behavior of the shared shell.

## Option C — Keep the navbar unchanged and rely on page-local filters or headings only
- Pros:
  - Smallest visual change.
  - Leaves the existing activity filter chips as the only selected-state UI for activity subsections.
  - Avoids touching the shared header.
- Cons:
  - Does not satisfy the request to make the navbar itself show the selected page or section.
  - Leaves top-level navigation weaker on non-activity pages.
  - Keeps the current navigation state split between the shared nav and page-local controls.

## Recommendation
Recommend Option A: add a shared server-rendered active-nav contract and have the primary nav mark the matching section active.

This is the smallest coherent slice because the request is about the shared navbar, not just page-local filters. A server-rendered section state keeps the UI correct on first paint, aligns with the existing shared header architecture, and cleanly treats all `/activity/` filtered views as one selected top-level section.
