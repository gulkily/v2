## Problem Statement
Choose the smallest useful way to add a read-only plain-text HTTP API on top of the current renderer and canonical post files without collapsing this loop into a full backend-contract rewrite.

### Option A: Add plain-text API routes inside the existing WSGI app
- Pros:
  - Fastest path to a demonstrable agent-friendly interface.
  - Reuses the post loading, thread grouping, and lookup logic already proven by the web renderer.
  - Keeps Loop 3 scoped to read-only API behavior only.
- Cons:
  - May need refactoring later when the CGI-style contract is split into language-specific scripts.
  - Risks some coupling between browser routes and API routes if boundaries are not kept clean.

### Option B: Implement the read API as separate CGI-style endpoint scripts now
- Pros:
  - Aligns earlier with the long-term multi-language backend model.
  - Makes the API contract feel more explicit from the start.
  - Reduces later extraction work if CGI remains the final execution shape.
- Cons:
  - Larger scope for this loop.
  - Introduces execution and routing complexity before the read contract is proven useful.
  - Slows down the first agent-facing demo.

### Option C: Export read-only plain-text snapshots as generated files
- Pros:
  - Very simple serving model.
  - Makes outputs easy to inspect and diff.
  - Could be useful later as fixtures.
- Cons:
  - Weak fit for an actual HTTP API contract.
  - Adds generation steps instead of direct repository reads.
  - Does not prove the live request/response behavior the checklist calls for.

## Recommendation
Recommend Option A: add plain-text API routes inside the existing WSGI app.

It is the smallest slice that makes the forum accessible to agents and CLI users while preserving the loop boundary. The next feature should prove the read contract and payload shapes first, then later loops can extract or parallelize the backend execution model without rethinking the data access logic.
