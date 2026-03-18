## Problem
The current PHP-host missing-config failure is technically correct but operationally weak: it shows a raw missing-file message without guiding an admin through the fastest recovery path. The next slice should replace that failure with a clearer, nicer diagnostic page that helps an operator restore a valid `forum_host_config.php` setup without changing the thin PHP adapter model.

## User Stories
- As an operator, I want the missing-config failure page to clearly explain what is wrong so I can fix the deployment quickly.
- As an operator, I want the page to show the expected recovery command and next steps so I do not have to cross-reference multiple docs while the site is down.
- As an operator, I want the page to feel intentional and readable rather than like a raw crash so I can distinguish a setup issue from an application bug.
- As a maintainer, I want the handler to preserve explicit failure instead of guessing defaults so broken deployments remain easy to diagnose.
- As a maintainer, I want this slice to reuse the existing PHP-host setup workflow and documentation rather than adding a second configuration path.

## Core Requirements
- The slice must replace the current raw missing-config output with one dedicated admin-facing diagnostic page for the missing `forum_host_config.php` case.
- The page must clearly identify the missing config include, the checked or expected path, and the primary recovery action using the existing `./forum php-host-setup` workflow.
- The page must present recovery guidance in a readable, polished layout that feels like a deliberate product surface rather than an unformatted fatal error.
- The handler must keep failure explicit and must not fall back to example config, guessed defaults, or degraded runtime behavior when the real config is missing.
- The slice must keep scope narrow: improve the missing-config experience only, without redesigning the broader PHP-host installation model.

## Shared Component Inventory
- PHP adapter entrypoint: extend [index.php](/home/wsl/v2/php_host/public/index.php) as the canonical missing-config handler surface, because that is where the failure is currently detected and rendered.
- PHP-host setup workflow: reuse the existing `./forum php-host-setup` operator flow as the canonical recovery action rather than introducing a second repair path.
- Installation documentation: reuse and extend [php_primary_host_installation.md](/home/wsl/v2/docs/php_primary_host_installation.md) as the canonical long-form reference, with the error page pointing back to it when needed.
- Generated PHP host config contract: preserve [forum_host_config.php](/home/wsl/v2/php_host/public/forum_host_config.php) as the required host-local include rather than replacing it with request-time defaults.
- New UI/API surfaces: none; this is an improvement to an existing failure surface, not a new product page.

## Simple User Flow
1. An operator deploys or visits a PHP-hosted installation where `forum_host_config.php` is missing.
2. The PHP adapter renders a structured diagnostic page instead of a raw plain-text failure.
3. The page explains that the config include is missing, shows the expected location, and highlights the recommended recovery command.
4. The operator runs the existing setup workflow or fixes the host-local file placement.
5. The operator reloads the site and reaches the normal forum surface once the config include is present.

## Success Criteria
- A missing PHP host config now produces a readable, intentional diagnostic page instead of the current raw two-line failure.
- An operator can identify the missing file and the recommended recovery command directly from the page without needing source-code inspection.
- The page makes the primary repair path obvious enough that a maintainer can distinguish configuration mistakes from runtime application failures quickly.
- The handler remains explicit: installs with no real `forum_host_config.php` still fail closed rather than attempting fallback defaults.
- The slice stays limited to the missing-config experience and does not expand into broader install-flow redesign.
