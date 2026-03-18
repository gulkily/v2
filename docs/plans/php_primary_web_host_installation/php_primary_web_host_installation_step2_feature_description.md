## Problem
The application already runs as a Python-based web and CGI-style system, but operators on PHP-primary hosts still lack a credible install path when the host expects PHP entry files and Apache-style directory controls. The next slice should define the smallest useful installation shape for those hosts by adding a minimal PHP shim and allowing `.htaccess`-based routing/configuration without changing the application's canonical Python behavior.

## User Stories
- As an operator, I want to install this application on a PHP-primary web host so that I can publish it without needing a VPS-style Python process manager.
- As an operator, I want the install path to use familiar host primitives such as `index.php`, `.htaccess`, and `cgi-bin` so that it fits common shared-host workflows.
- As a maintainer, I want the existing Python read and write contracts to remain canonical so that PHP-host support does not create a second application behavior model.
- As a future backend implementer, I want the hosting adapter to stay thin so that deployment-specific glue does not redefine forum semantics.

## Core Requirements
- The slice must support one documented PHP-primary installation profile built around a minimal PHP shim plus `.htaccess` directives where needed.
- The slice must preserve the current canonical application behavior for existing read routes and CGI-style write commands rather than reimplementing forum logic in PHP.
- The slice must define the minimum host capabilities required for this installation profile, including PHP support and any required CGI/script execution assumptions.
- The slice must keep the operator setup narrow and reproducible, covering the public web entry path, routing behavior, and the connection from PHP-host-facing requests into the existing Python surfaces.
- The slice must avoid a PHP-native rewrite, alternate repository format, parallel API contract, or host-specific matrix spanning multiple unrelated deployment models.

## Shared Component Inventory
- Existing read web surface: reuse the current WSGI application in `forum_web/web.py` as the canonical renderer for forum pages; the PHP-facing layer is an adapter, not a new page system.
- Existing write command surface: reuse `cgi-bin/create_thread.py` and `cgi-bin/create_reply.py` as the canonical write entrypoints; the PHP-host installation path must not redefine their payload or response contracts.
- Existing browser posting surface: reuse the current compose and browser-signing flows that already target `/api/create_thread` and `/api/create_reply`; host support should preserve these endpoints rather than introducing PHP-specific submission URLs.
- Existing runtime configuration surface: reuse the current environment and repo-root configuration model instead of adding a PHP-only settings mechanism.
- Existing operator documentation surface: extend repo documentation with one PHP-primary host installation guide because this feature is primarily an install and deployment story, not a product-surface expansion.
- New UI/API surfaces: none beyond the minimal host adapter entrypoint needed to expose the existing application on a PHP-primary host.

## Simple User Flow
1. An operator uploads the repo and the PHP-host adapter files to a PHP-primary web host.
2. The operator applies the documented `.htaccess` and host-directory layout for the public entry path and any required CGI script locations.
3. The host receives a browser request through the PHP-facing entrypoint.
4. The adapter routes the request into the existing Python-backed read or write surface without changing the canonical forum contract.
5. The operator verifies that the forum loads, existing compose flows still submit to the same endpoints, and repository-backed state behaves as expected on the hosted instance.

## Success Criteria
- An operator can follow one documented PHP-primary host installation path using a minimal PHP shim and `.htaccess` directives.
- The hosted instance serves the existing forum read experience without requiring a long-running Python app server under operator control.
- Existing write flows still target the canonical `create_thread` and `create_reply` contracts rather than a PHP-specific alternative.
- The deployment story clearly states the minimum host capabilities and excludes unsupported PHP-only environments that cannot invoke the required Python surfaces.
- The resulting adapter remains thin enough that future feature work continues to target the canonical Python application and CGI contracts first.
