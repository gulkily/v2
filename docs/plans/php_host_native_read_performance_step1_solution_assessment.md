## Problem Statement
Choose the smallest coherent way to make the PHP-hosted production path serve core read pages faster while reducing reliance on per-request Python CGI execution.

### Option A: Push harder on the existing PHP shim cache and static-HTML strategy while keeping Python as the only renderer
- Pros:
  - Smallest change to the current architecture because Python remains the only canonical page renderer.
  - Builds directly on existing PHP microcache, generated static HTML, and PHP-host refresh workflows.
  - Keeps duplicate business logic to a minimum.
- Cons:
  - Still leaves cold misses and dynamic read paths dependent on Python CGI startup and render cost.
  - Performance wins are capped because PHP remains mostly a cache wrapper around Python.
  - Does not materially advance the longer-term duplicate-code-path strategy.

### Option B: Reimplement a narrow allowlist of hot anonymous read paths in PHP against shared derived artifacts
- Pros:
  - Targets the highest-traffic pain directly by letting PHP answer selected board, thread, post, or profile reads without Python on cache misses.
  - Fits the duplicate-code-path strategy without forcing a full fork of the application.
  - Keeps Python authoritative for writes and for producing shared derived/indexed data that PHP can consume.
  - Gives a clearer path to measurable latency reduction on the public production path.
- Cons:
  - Requires strict boundaries so PHP and Python do not drift on routing, visibility, and read-model semantics.
  - Needs careful choice of which pages are safe enough and hot enough to justify duplicate rendering logic.
  - Introduces some ongoing maintenance cost because two runtimes now participate in read behavior.

### Option C: Build a broad PHP-native front end that duplicates most read rendering and request logic
- Pros:
  - Maximizes the chance that PHP-hosted traffic avoids Python for ordinary reads.
  - Pushes furthest toward a true multi-runtime strategy.
- Cons:
  - Highest implementation and regression risk.
  - Easy to create a long-term fork where read behavior diverges between Python-hosted and PHP-hosted deployments.
  - Larger than the current performance problem requires.

## Recommendation
Recommend Option B: reimplement a narrow allowlist of hot anonymous read paths in PHP against shared derived artifacts, while keeping Python authoritative for writes and shared data preparation.

This is the smallest option that can materially improve PHP-host performance and also exercise the duplicate-code-path strategy on purpose rather than by accident. Step 2 should stay strict about boundaries: identify the exact hot public read routes, define the shared derived data or artifact contract PHP will consume, and leave writes, cache invalidation authority, and non-allowlisted routes on the current Python path.
