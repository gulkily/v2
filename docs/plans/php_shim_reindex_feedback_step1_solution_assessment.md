## Problem Statement
Choose the smallest coherent way to give users immediate feedback during request-triggered post-index rebuilds when production traffic is served through Apache and the PHP shim, which currently buffers the full CGI response before sending it.

### Option A: Redesign the PHP shim and CGI gateway to support true incremental streaming
- Pros:
  - Preserves the same-request waiting-page model on the actual production path.
  - Keeps the user experience conceptually aligned with the long-lived Python host.
- Cons:
  - High implementation and operational risk for a feedback fix.
  - Requires careful changes across Apache/PHP/CGI buffering boundaries, not just application code.
  - Hard to validate reliably because each buffering layer can partially defeat the design.

### Option B: Keep the PHP path buffered and switch to a PHP-compatible degraded response during rebuilds
- Pros:
  - Matches the confirmed production reality: the public path is Apache -> PHP shim and does not stream.
  - Solves the user-facing stall by returning an immediate lightweight status page instead of waiting for the rebuilt destination page.
  - Keeps the change inside the current deployment model without requiring web-server streaming guarantees.
- Cons:
  - The degraded page must hand control back to a follow-up request rather than completing inside one streamed response.
  - Needs a reliable way to detect and report "rebuild in progress" on the PHP path.

### Option C: Remove request-triggered rebuilds from the PHP path and require operator-driven rebuilds
- Pros:
  - Simplest runtime model.
  - Avoids long user-facing waits on the public path.
- Cons:
  - Changes product behavior more than the current feedback problem requires.
  - Leaves normal reads stale or unavailable until an external rebuild happens.

## Recommendation
Recommend Option B: keep the PHP path explicitly buffered and design a PHP-compatible degraded response for index rebuilds instead of trying to force true streaming through Apache/PHP/CGI.

This is the smallest option that fits the production architecture we just confirmed. The next steps should define an immediate status response that the PHP shim can return without waiting for the final rebuilt page, plus a narrow contract for how follow-up requests detect rebuild progress and resume normal rendering once the index is ready.
