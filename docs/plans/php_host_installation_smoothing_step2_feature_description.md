## Problem
The PHP-primary installation profile works, but operators still have to copy files, hand-edit host-specific paths, and keep the public web root in sync with repo-managed adapter files. The next slice should make that install path more repeatable by generating one host-local PHP config include, providing a tracked example for it, and attempting symlink-based publication of the PHP host entry files without changing the canonical Python application boundary.

## User Stories
- As an operator, I want one setup command to generate the host-local PHP adapter config so I do not have to hand-edit fragile absolute paths in the public web root.
- As an operator, I want the real host config file to stay ignored by git while a repo-tracked example shows the expected shape and keys.
- As an operator, I want the setup command to symlink the required PHP host files into the web root when the host allows it so repo-managed adapter updates do not require repeated manual copying.
- As a maintainer, I want the PHP shim to keep reading explicit host-local configuration rather than adding request-time autodiscovery so deployment behavior stays debuggable.
- As a maintainer, I want this slice to stay an installation smoother for the existing adapter rather than turning into a general-purpose deployment framework.

## Core Requirements
- The slice must add one repo-tracked example PHP config include and one generated real PHP config include that is ignored by git.
- The generated real config include must hold only host-local adapter settings such as deployed application root, forum repository root, cache directory, and other PHP-host runtime path values needed by the existing shim.
- The setup workflow must generate or refresh the real config include from repo-managed inputs, automatically filling values it can derive and prompting the operator only for missing or ambiguous values.
- The PHP front controller and any companion PHP helper files must read adapter configuration from that generated include rather than requiring direct host-side environment-variable editing as the primary setup path.
- The setup workflow must attempt to create symlinks in the target public web root for `index.php`, `.htaccess`, and the generated config include.
- The setup workflow must stay idempotent: rerunning it should refresh generated content and repair expected symlinks without creating duplicate files or changing unrelated host content.
- The slice must define a clear fallback when symlink creation is unavailable or denied, while keeping the symlink-first path as the preferred supported flow.
- The slice must keep the canonical Python read and write surfaces unchanged and must not move deployment discovery logic into request-time PHP behavior.
- The slice must avoid becoming a broader deploy tool for virtual hosts, TLS, databases, process managers, or unsupported PHP-only environments.

## Shared Component Inventory
- PHP adapter entrypoint: extend [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php) so it loads host-local adapter configuration from a generated include instead of relying on direct inline host edits or environment setup as the main operator experience.
- PHP adapter rewrite rules: keep [`php_host/public/.htaccess`](/home/wsl/v2/php_host/public/.htaccess) as a repo-managed public entry artifact that the setup workflow publishes into the web root.
- PHP adapter cache helper: preserve [`php_host/public/cache.php`](/home/wsl/v2/php_host/public/cache.php) as adapter-only behavior; this slice may let it consume generated config values, but it must not change the canonical cache boundary.
- Install documentation: update [`docs/php_primary_host_installation.md`](/home/wsl/v2/docs/php_primary_host_installation.md) so the supported install profile uses generated config plus symlinked public files instead of copy-and-edit instructions.
- Ignore rules: extend [`.gitignore`](/home/wsl/v2/.gitignore) so the generated real PHP host config include is never tracked.
- Operator command surface: add one repo-managed setup command in the existing `./forum` command direction to generate the config include and publish the three public files.
- Canonical Python surfaces: reuse the current WSGI and CGI entrypoints unchanged; this feature smooths installation only and does not redefine route or write behavior.
- New UI/API surfaces: none.

## Simple User Flow
1. An operator runs the repo-managed PHP-host setup command and provides the target public web root.
2. The setup workflow derives known paths from the current checkout and prompts for any required values it cannot determine safely.
3. The workflow writes or refreshes a real ignored PHP config include from the repo-tracked example shape.
4. The workflow attempts to symlink `index.php`, `.htaccess`, and the generated config include into the public web root.
5. If symlinks are unavailable, the workflow reports the supported fallback and leaves the operator with a complete generated config file plus explicit next steps.
6. The operator requests `/` through the PHP-hosted path and verifies the existing forum read and write surfaces still behave canonically.

## Success Criteria
- An operator can prepare the PHP-host installation through one repo-managed setup workflow without hand-authoring the real host-local PHP config file.
- The repo contains a tracked example PHP config include, while the generated real config include is ignored by git.
- The PHP front controller uses the generated config include as the primary source for host-local adapter settings.
- The setup workflow can derive obvious local values automatically and prompts only for inputs it cannot determine reliably.
- The workflow successfully symlinks `index.php`, `.htaccess`, and the real config include into the public web root on hosts that allow symlinks.
- Hosts that do not allow symlinks receive a documented fallback path that still preserves the generated config contract and keeps public-file drift explicit.
- The resulting installation model remains a thin PHP adapter over the canonical Python application rather than a new deployment/runtime layer.
