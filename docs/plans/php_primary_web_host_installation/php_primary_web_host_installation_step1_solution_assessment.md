## Problem Statement
Choose the smallest credible way to let an operator install this application on a PHP-primary web host without changing the product into a PHP-native application.

### Option A: Support PHP-primary hosting through a documented Python CGI deployment profile
- Pros:
  - Matches the repo's existing CGI-style write entrypoints and keeps the current Python implementation canonical.
  - Fits shared hosts and PHP-first environments that allow `cgi-bin`, Python scripts, and basic rewrite rules.
  - Keeps the scope centered on installation packaging, routing, environment setup, and operator docs rather than a runtime rewrite.
  - Preserves the language-neutral CGI direction already described elsewhere in the project.
- Cons:
  - Depends on the host allowing Python CGI execution, not just PHP alone.
  - May need clear constraints around filesystem layout, executable permissions, and git availability on the host.
  - Could require a degraded or explicitly scoped setup if long-running WSGI processes are unavailable.

### Option B: Require a separate Python app process behind the PHP host's web server
- Pros:
  - Closer to a typical Python deployment and likely simpler operationally on VPS-style hosts.
  - Avoids CGI performance and timeout constraints.
  - Keeps request handling unified under the existing WSGI surface.
- Cons:
  - Misses the user story's PHP-primary host target for many shared-host operators.
  - Assumes shell access, process management, and reverse-proxy control that PHP-first hosts often do not provide.
  - Turns the "PHP-primary" ask into "use a Python host that happens to serve PHP too."

### Option C: Build a PHP-native shim or parallel PHP implementation
- Pros:
  - Would run on the broadest set of PHP-only hosts.
  - Could make installation feel more conventional for PHP-focused operators.
- Cons:
  - Introduces a second backend implementation far beyond the scope of an installation feature.
  - Risks behavioral drift from the canonical Python/CGI contracts.
  - Delays operator value by turning a deployment problem into a rewrite project.

## Recommendation
Recommend Option C: build a minimal PHP shim for PHP-primary hosts.

This is the only option that squarely targets operators on PHP-first hosts that may not expose Python CGI or process control directly. The next steps should keep the shim extremely narrow: use PHP only as the thin web-facing adapter, preserve the existing Python contracts and repository behavior behind it, and explicitly avoid turning this slice into a parallel PHP reimplementation.
