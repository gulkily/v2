# Developer Commands

Use `./forum` as the short repo-root command for common local tasks.

## Common tasks
- `./forum help`: show the available subcommands.
- `./forum install`: install required Python packages into the user profile.
- `./forum install --target venv`: install into a repo-local `.venv`.
- `./forum install --target current`: install into the current Python environment.
- `./forum env-sync`: append missing `.env` settings from `.env.example` without overwriting existing values.
- `./forum git-recover`: diagnose the current checkout for common deploy-sync git failures.
- `./forum git-recover --apply`: reset the checkout back to local `main` tracking `origin/main`, discarding local commits and working-tree changes when needed.
- `./forum content-purge records/posts`: preview archival-plus-history purge for one or more canonical `records/` paths.
- `./forum content-purge records/posts --apply --archive-output /tmp/forum-posts.zip`: archive the selected content outside the repo and rewrite reachable history to remove it.
- `./forum rebuild-index`: force a full rebuild of the derived post index for the current checkout.
- `./forum php-host-setup /absolute/path/to/public-web-root`: generate PHP-host config and publish the required public files into a PHP web root.
- `./forum start`: run the local read-only forum server.
- `./forum test`: run the full unittest suite.
- `./forum test test_profile_update_page.py`: run one unittest discovery pattern.

The command contract is intentionally small: future backends such as Perl should preserve the same subcommands and high-level behavior.

## Git recovery
- `./forum git-recover` is the canonical operator diagnosis path when a checkout is failing normal `git pull`.
- `--apply` resets the checkout to the expected deployment state and may discard local commits, staged changes, tracked edits, and untracked files to get back to `origin/main`.
- Mid-operation states such as rebase-in-progress and merge-in-progress are diagnosed, but still require explicit operator resolution before rerunning `--apply`.

## Content purge
- `./forum content-purge <records-path> [...]` previews an operator-only archive-plus-history-rewrite workflow for canonical content under `records/`.
- Supported selections are repository-relative paths beneath `records/`, such as `records/posts`, `records/identity`, or another specific record family or file.
- The command rejects the `records/` root itself, non-`records/` paths, duplicate selections, and overlapping selections such as `records/posts` plus `records/posts/root-001.txt`.
- `--apply` performs the destructive path only after the preview contract is satisfied.
- `--archive-output` must point outside the repository root so the export artifact does not dirty the repo being rewritten.
- `--apply` requires a clean worktree unless `--force` is used explicitly.
- Real apply mode requires the `git-filter-repo` executable on `PATH`.
- After a successful apply run, operators must force-push rewritten refs and retire or reclone old checkouts; the command prints those follow-up steps explicitly.

## Direct entrypoints still supported
- `python3 scripts/forum_tasks.py ...`: direct Python reference runner.
- `python3 scripts/run_read_only.py`: direct local server entrypoint.
- `python3 -m unittest discover -s tests [-p PATTERN]`: direct test invocation.
- `cgi-bin/create_thread.py` and `cgi-bin/create_reply.py`: direct write-command entrypoints for lower-level testing and parity work.

## Runtime environment
- `./forum install` is the canonical first-run bootstrap command for a clean shell account.
- The default install target is the user profile; use `--target venv` for a repo-local `.venv` or `--target current` for the current Python environment.
- Repo-root `.env` is loaded automatically for the main local server path, direct WSGI import path, CGI write entrypoints, and `./forum test`.
- Run `./forum env-sync` after pulling changes that add new keys to `.env.example`.
- Restart the relevant process after changing `.env`.
- Explicit process environment variables still override `.env`.
- `FORUM_HOST` and `FORUM_PORT` control the local server bind address for `./forum start`.
- `DEDALUS_API_KEY` enables the server-side `/api/call_llm` baseline LLM endpoint.
- `FORUM_ENABLE_THREAD_AUTO_REPLY=1` enables one best-effort Dedalus-generated assistant reply after successful thread creation.
- `FORUM_THREAD_AUTO_REPLY_PRIVATE_KEY_PATH` and `FORUM_THREAD_AUTO_REPLY_PUBLIC_KEY_PATH` are optional overrides for the assistant's ASCII-armored signing key files. If they are unset or missing, the server will try to generate key files automatically.
- The wrapper prefers `.venv/bin/python3` when present and otherwise falls back to `python3`.

## Public instance info
- The public `/instance/` page publishes operator, policy, and deployment facts for the current instance.
- Tracked public metadata lives in `records/instance/public.txt`.
- Commit ID and commit date are derived from the current git checkout at render time.
- Moderation settings are derived from the current moderator allowlist configuration.

## PHP-primary host profile
- The supported PHP-primary deployment profile is documented in [php_primary_host_installation.md](/home/wsl/v2/docs/php_primary_host_installation.md).
- The documented source checkout for that profile is `https://github.com/gulkily/v2`.
- Run `./forum php-host-setup /absolute/path/to/public-web-root` from the deployed checkout to generate `php_host/public/forum_host_config.php` and symlink `index.php`, `.htaccess`, and `forum_host_config.php` into the public web root when the host allows symlinks.
- Keep `php_host/public/forum_host_config.example.php` tracked as the example shape and let `php_host/public/forum_host_config.php` remain ignored as host-local state.
- If the host rejects symlinks, follow the command output for the manual fallback instead of editing `index.php` directly.
- The PHP adapter keeps the existing `/api/create_thread` and `/api/create_reply` routes intact rather than introducing PHP-specific write endpoints.

## Dedalus baseline
1. Install dependencies with `./forum install`.
2. Run `./forum env-sync` and set `DEDALUS_API_KEY=...` in the repo-root `.env`.
3. Start the local server with `./forum start`.
4. Call the baseline LLM endpoint:

```bash
curl -s http://127.0.0.1:8000/api/call_llm \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Reply with the single word ready.","system_prompt":"Be concise."}'
```

The response is `text/plain` and includes the command name, model, and generated output.

## Thread auto reply
1. Install dependencies with `./forum install`.
2. Run `./forum env-sync`.
3. Set `DEDALUS_API_KEY=...` and `FORUM_ENABLE_THREAD_AUTO_REPLY=1` in the repo-root `.env`.
4. Optionally set `FORUM_THREAD_AUTO_REPLY_PRIVATE_KEY_PATH=...` and `FORUM_THREAD_AUTO_REPLY_PUBLIC_KEY_PATH=...` if you want the assistant signing keys somewhere specific. If you leave them unset, the server will try to create them under `records/system/`.
5. Restart the relevant process after changing `.env`.
6. Create a thread through the usual browser or `/api/create_thread` flow.

When enabled, the server stores the root thread first and then makes one best-effort attempt to add a canonical assistant reply beneath it. `/api/create_thread` reports `Auto-Reply-Status` in its plain-text response. The preferred path is a signed assistant reply. If assistant key files are missing, the server will try to generate them automatically; if signing setup still fails, it falls back once to an unsigned reply instead of dropping the generated comment. If the LLM call itself fails, the original thread still succeeds and remains stored.

The stored auto-reply now includes visible provenance in the reply itself:
- the reply subject is `model-generated reply (<model>)`
- the reply body begins with `[Model-generated reply via <model>]`

Prompt location for this feature:
- The user prompt is built in [auto_reply.py](/home/wsl/v2/forum_cgi/auto_reply.py) by `build_thread_auto_reply_prompt(...)`.
- The system instruction is the inline `"role": "system"` message inside `generate_thread_auto_reply(...)` in the same file.
