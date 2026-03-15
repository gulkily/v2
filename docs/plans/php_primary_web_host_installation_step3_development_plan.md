## Stage 1
- Goal: define the supported PHP-primary host profile and the minimal adapter contract before adding files.
- Dependencies: approved Step 2; current WSGI read surface; current CGI write entrypoints; allowed `.htaccess` usage.
- Expected changes: add one operator-facing hosting profile document that states the minimum host capabilities, public-web-root layout, unsupported environments, and the thin-adapter boundary; define the minimal shim contract conceptually, including a PHP entry surface such as `dispatch_forum_request(): void` or equivalent request-forwarding behavior; no database changes.
- Verification approach: review the documented profile against the current repo entrypoints and confirm every required host feature maps to an existing Python read or write surface.
- Risks or open questions:
  - whether the supported host profile assumes Python CGI only, or also requires shell execution from PHP
  - choosing one install shape narrow enough to be supportable on shared hosts
- Canonical components/API contracts touched: `forum_read_only.web` WSGI contract; `cgi-bin/create_thread.py`; `cgi-bin/create_reply.py`; new PHP-primary operator install guide.

## Stage 2
- Goal: add the minimal PHP-facing read adapter and Apache-style routing files for the public site surface.
- Dependencies: Stage 1; existing read-only route contract in `forum_read_only.web`.
- Expected changes: add a small PHP entry file plus any companion adapter script/config needed to forward HTTP requests into the canonical Python read surface, add `.htaccess` directives for front-controller routing and static-path exclusions, and define any required environment/path handoff variables; planned signatures/contracts: one thin PHP request dispatcher and one stable mapping from incoming request method/path/query to the existing read app behavior.
- Verification approach: manually request `/`, a thread page, and a static asset path through the adapter and confirm the routed responses match the current read-only app behavior.
- Risks or open questions:
  - avoiding host-specific rewrite assumptions that break on common Apache shared-host defaults
  - keeping the shim thin instead of reproducing routing logic in PHP
- Canonical components/API contracts touched: public route contract from `forum_read_only.web`; PHP front-controller entrypoint; `.htaccess` rewrite behavior.

## Stage 3
- Goal: preserve canonical write behavior for compose and `/api/` submission flows under the PHP-primary hosting profile.
- Dependencies: Stage 2; existing `/api/create_thread` and `/api/create_reply` contracts; current CGI entrypoint behavior.
- Expected changes: route write requests either directly to the existing CGI scripts or through the same thin adapter without changing payload/response semantics, document the host-directory and executable placement for `cgi-bin`, and define any adapter boundary needed so browser compose flows keep posting to the canonical endpoints; planned signatures/contracts: no new write API, only adapter behavior that preserves `POST /api/create_thread` and `POST /api/create_reply`.
- Verification approach: submit one thread and one reply through the hosted path and confirm the responses, stored records, and resulting readback match the current canonical behavior.
- Risks or open questions:
  - whether the host allows CGI execution under the same public tree or requires a separate script directory
  - avoiding divergence between PHP-routed read paths and CGI-routed write paths
- Canonical components/API contracts touched: `/api/create_thread`; `/api/create_reply`; existing compose/browser-signing submission flow; `forum_cgi.entrypoint`.

## Stage 4
- Goal: lock the PHP-primary install path into focused verification coverage and operator documentation.
- Dependencies: Stages 1-3.
- Expected changes: add focused tests around any new request/path translation helpers, add a minimal local smoke harness if needed for the adapter-facing contract, and publish the installation steps, `.htaccess` example, required permissions, and post-install checks in the repo docs; no database changes.
- Verification approach: run targeted tests for any new adapter helpers, perform one end-to-end hosted smoke pass covering read pages and write endpoints, and confirm the documented setup exactly matches the implemented file layout and routing behavior.
- Risks or open questions:
  - choosing a test seam that exercises adapter behavior without requiring a real shared-host environment in CI
  - keeping the documentation specific enough to be actionable without implying support for every PHP host variant
- Canonical components/API contracts touched: adapter helper tests; PHP-primary installation guide; `.htaccess` example contract; canonical read and write endpoint documentation.
