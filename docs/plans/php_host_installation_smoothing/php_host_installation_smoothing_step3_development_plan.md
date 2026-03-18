## Stage 1
- Goal: define the generated PHP host-config contract and expose one repo-managed setup command for this install profile.
- Dependencies: approved Step 2; existing task runner in [`scripts/forum_tasks.py`](/home/wsl/v2/scripts/forum_tasks.py); current PHP-host artifacts in [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php) and [`php_host/public/.htaccess`](/home/wsl/v2/php_host/public/.htaccess).
- Expected changes: add one `./forum` subcommand for PHP-host setup, add a repo-tracked example PHP config include plus the matching generated real config filename/shape, and extend [`.gitignore`](/home/wsl/v2/.gitignore) so the generated config is never tracked; planned contracts should stay narrow, for example `forum php-host-setup <public-web-root>` or equivalent plus helper functions that derive defaults, prompt for unresolved values, and render the config include from repo-managed inputs; no database changes.
- Verification approach: run the new setup command against a temporary target directory, confirm it derives obvious repo-local paths automatically, prompts only for unresolved values, and writes the ignored real config include in the expected shape.
- Risks or open questions:
  - choosing a config-file location/name that is easy for PHP to require while remaining safe to ignore in git
  - keeping the command interaction scriptable enough for repeat runs without turning it into a large deployment framework
- Canonical components/API contracts touched: `./forum` operator command surface; PHP-host config contract only; canonical Python read/write behavior remains unchanged.

## Stage 2
- Goal: update the PHP adapter to consume the generated host-local config include as its primary runtime source.
- Dependencies: Stage 1; current PHP adapter entrypoint and helper files in [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php) and [`php_host/public/cache.php`](/home/wsl/v2/php_host/public/cache.php).
- Expected changes: add one repo-tracked example include and one real generated include shape, teach the PHP front controller and any companion helper files to `require` that config file, and move adapter-local settings such as app root, repo root, and cache directory lookups behind the loaded config rather than direct env editing as the main operator path; planned PHP contracts may include helpers such as `forum_host_config(): array`, `forum_app_root(): string`, and cache helpers that read from loaded config with narrowly scoped environment fallbacks if needed for compatibility; no database changes.
- Verification approach: run `php -l` on modified PHP files, execute the PHP front controller with a generated config include present, and confirm `/`, one thread route, and one asset route still resolve through the canonical Python surface.
- Risks or open questions:
  - preserving backward compatibility for any current env-based local smoke workflows without letting env remain the undocumented primary install path
  - ensuring the generated config include contains only deployment-local values and no duplicated application logic
- Canonical components/API contracts touched: PHP shim request-forwarding contract; PHP-host cache helper contract; canonical Python rendering and write endpoints stay unchanged.

## Stage 3
- Goal: implement symlink-first publication of the three required public files and define the fallback path for hosts that reject symlinks.
- Dependencies: Stages 1-2; generated config contract; target public artifacts `index.php`, `.htaccess`, and the real generated config include.
- Expected changes: extend the setup command so it attempts to create or repair symlinks in the chosen public web root for the three required files, reports what it changed, and handles reruns idempotently; define a narrow fallback behavior for symlink failures, such as emitting explicit copy/manual-link instructions or optionally performing a one-time copy only if that fallback is intentionally approved in the implementation, while keeping symlinks as the preferred supported path; no database changes.
- Verification approach: run the setup command against a temporary public root, confirm the expected symlinks are created, rerun the command to confirm it repairs or preserves correct links without duplication, and simulate a non-symlink fallback case closely enough to verify the reported operator guidance.
- Risks or open questions:
  - deciding whether the initial fallback should be documentation-only or an automated copy mode
  - handling existing non-symlink files in the public root safely without overwriting unrelated operator content
- Canonical components/API contracts touched: `./forum` PHP-host setup workflow; public artifact publication contract only; canonical route/write behavior remains unchanged.

## Stage 4
- Goal: lock the new install workflow into focused verification coverage and operator documentation.
- Dependencies: Stages 1-3; current operator guide in [`docs/php_primary_host_installation.md`](/home/wsl/v2/docs/php_primary_host_installation.md).
- Expected changes: add targeted tests around the new setup-command helpers and any config-rendering/path-publication behavior that can be exercised locally, update the PHP-primary installation doc to describe generated config, ignored-file ownership, symlink-first setup, fallback behavior, and post-install checks, and record the delivered work in the Step 4 implementation summary; no new runtime surfaces or database changes.
- Verification approach: run the targeted tests for the setup workflow, run the command end-to-end against temporary directories, then perform one PHP-host smoke pass covering generated-config loading, public-file publication, cached read behavior still working, and one write flow still invalidating cached reads correctly.
- Risks or open questions:
  - choosing a test seam that verifies symlink behavior and prompting logic without making the suite brittle across environments
  - keeping the install guide specific enough to prevent drift while not implying support for broader shared-host automation
- Canonical components/API contracts touched: `./forum` command help/usage contract; PHP-primary installation guide; existing PHP shim and cache behavior; canonical Python read/write endpoint contracts only.
