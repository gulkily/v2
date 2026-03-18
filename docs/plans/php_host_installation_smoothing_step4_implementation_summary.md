## Stage 1 - Add the PHP-host setup command and generated config contract
- Changes:
  - Added [php_host_setup.py](/home/wsl/v2/forum_core/php_host_setup.py) with the PHP-host setup request/config models, derived path defaults, config rendering, and public-file publication helpers.
  - Extended [forum_tasks.py](/home/wsl/v2/scripts/forum_tasks.py) with the `./forum php-host-setup <public-web-root>` subcommand plus optional path overrides and a `--non-interactive` mode for repeatable runs.
  - Added the tracked example config include at [forum_host_config.example.php](/home/wsl/v2/php_host/public/forum_host_config.example.php) and updated [`.gitignore`](/home/wsl/v2/.gitignore) so the generated real [forum_host_config.php](/home/wsl/v2/php_host/public/forum_host_config.php) stays untracked.
- Verification:
  - Ran `python3 -m py_compile forum_core/php_host_setup.py scripts/forum_tasks.py tests/test_forum_tasks.py tests/test_php_host_cache.py`.
  - Ran `./forum help` and confirmed `php-host-setup` appears in the canonical command help output.
  - Ran `./forum test test_forum_tasks.py`; passed all 5 tests, including the new `php-host-setup` parse and symlink-publication coverage.
- Notes:
  - The generated config stays intentionally small: `app_root`, `repo_root`, `cache_dir`, and `microcache_ttl`.

## Stage 2 - Make the PHP adapter consume generated host-local config
- Changes:
  - Updated [index.php](/home/wsl/v2/php_host/public/index.php) to load `forum_host_config.php`, distinguish the repo source directory from the executed public script path, and pass the configured repo/app roots into the CGI environment.
  - Updated [cache.php](/home/wsl/v2/php_host/public/cache.php) so cache directory and TTL settings come from the generated config include, with narrow env fallbacks left in place for compatibility.
  - Kept the shim thin by confining the new behavior to config loading and path resolution rather than moving deployment autodiscovery into request-time routing.
- Verification:
  - Ran `php -l php_host/public/index.php`.
  - Ran `php -l php_host/public/cache.php`.
  - Ran `php -l php_host/public/forum_host_config.example.php`.
  - Ran `tmpdir=$(mktemp -d) && ./forum php-host-setup "$tmpdir" --non-interactive && REQUEST_METHOD=GET REQUEST_URI=/ QUERY_STRING= SERVER_NAME=localhost SERVER_PORT=80 SERVER_PROTOCOL=HTTP/1.1 SCRIPT_FILENAME=php_host/public/index.php php php_host/public/index.php | sed -n '1,5p'` and confirmed the PHP-hosted board index HTML rendered with the generated config in place.
- Notes:
  - The symlink-safe path fix in `index.php` was required so CLI-style smoke runs and deployed symlinked entrypoints resolve the same config file correctly.

## Stage 3 - Publish public files through symlink-first setup
- Changes:
  - Implemented symlink-first publication for `index.php`, `.htaccess`, and `forum_host_config.php` through [publish_php_host_public_files(...)](/home/wsl/v2/forum_core/php_host_setup.py).
  - Made reruns idempotent by preserving correct existing symlinks, replacing incorrect symlinks, and refusing to overwrite unrelated real files in the public web root.
  - Added explicit fallback notes when symlink creation fails so operators get manual next steps without the command silently drifting into unmanaged copies.
- Verification:
  - Ran `tmpdir=$(mktemp -d) && ./forum php-host-setup "$tmpdir" --non-interactive && find "$tmpdir" -maxdepth 1 -type l -printf '%f -> %l\n' | sort` and confirmed all three expected symlinks were created into the repo-managed `php_host/public/` sources.
  - Verified the new setup-command coverage in [test_forum_tasks.py](/home/wsl/v2/tests/test_forum_tasks.py) asserts the generated config file exists and the three public targets are symlinks after a non-interactive run.
- Notes:
  - The current fallback is intentionally explicit guidance, not an automated copy mode, so public-file drift remains visible.

## Stage 4 - Refresh docs and regression coverage
- Changes:
  - Updated [php_primary_host_installation.md](/home/wsl/v2/docs/php_primary_host_installation.md) to document the generated config contract, ignored real-config ownership, symlink-first installation steps, fallback expectations, and post-install checks.
  - Updated [developer_commands.md](/home/wsl/v2/docs/developer_commands.md) so `./forum php-host-setup` is part of the canonical operator command surface.
  - Updated [test_php_host_cache.py](/home/wsl/v2/tests/test_php_host_cache.py) so the PHP-host cache regression path now runs against the generated config include contract instead of direct env-only setup.
- Verification:
  - Ran `python3 -m unittest tests.test_php_host_cache`; passed all 3 tests.
  - Re-ran `./forum test test_forum_tasks.py`; passed all 5 tests.
  - Reviewed the updated installation and developer-command docs against the implemented command/config behavior to confirm they describe the same generated-file and symlink workflow.
- Notes:
  - The verification run generated an ignored local `php_host/public/forum_host_config.php`, which is expected for this workflow and remains untracked because of the new `.gitignore` rule.
