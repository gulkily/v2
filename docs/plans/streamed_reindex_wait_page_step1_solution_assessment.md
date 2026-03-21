## Problem Statement
Choose the smallest coherent way to show immediate reindex feedback without relying on a background process that may not survive request-scoped runtimes like CGI or the PHP shim.

### Option A: Stream a minimal waiting page from the same request on long-lived Python hosting, and keep CGI/PHP on a simpler non-streaming fallback
- Pros:
  - Matches the real constraint: no durable background work, but long-lived Python servers can still send UI feedback before rebuild completion.
  - Improves the user experience where the app can actually stream bytes early instead of pretending background execution exists.
  - Keeps the PHP/CGI boundary honest instead of shipping a design that only works accidentally in one runtime.
- Cons:
  - Requires runtime-specific behavior rather than one identical implementation everywhere.
  - Leaves PHP/CGI with a weaker experience until a separate durable worker or fallback path is designed.

### Option B: Keep rebuilds synchronous everywhere and only polish the existing blocking wait
- Pros:
  - Smallest implementation scope.
  - Avoids runtime-specific branching.
- Cons:
  - Does not solve the main UX problem if the browser still cannot render anything until the request is nearly done.
  - Keeps PHP/CGI and long-lived Python equally limited, even though the latter can do better.

### Option C: Stop request-triggered rebuilds and require explicit rebuilds outside normal reads
- Pros:
  - Cleanest operational model without background work.
  - Removes surprise rebuild latency from user requests.
- Cons:
  - Changes product behavior more than the current feedback problem requires.
  - Pushes the issue onto operators and can leave users with stale or unavailable reads.

## Recommendation
Recommend Option A: stream a minimal waiting page from the same request where the runtime supports it, and treat CGI/PHP as a separate fallback case rather than forcing fake parity.

This is the smallest option that actually improves the experience under the stated constraint. The next steps should stay narrow: deliver immediate streamed feedback for long-lived Python hosting, clearly define the non-streaming behavior for PHP/CGI, and avoid inventing a background-process story the deployment model cannot guarantee.
