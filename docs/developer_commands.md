# Developer Commands

Use `./forum` as the short repo-root command for common local tasks.

## Common tasks
- `./forum help`: show the available subcommands.
- `./forum env-sync`: append missing `.env` settings from `.env.example` without overwriting existing values.
- `./forum start`: run the local read-only forum server.
- `./forum test`: run the full unittest suite.
- `./forum test test_profile_update_page.py`: run one unittest discovery pattern.

The command contract is intentionally small: future backends such as Perl should preserve the same subcommands and high-level behavior.

## Direct entrypoints still supported
- `python3 scripts/forum_tasks.py ...`: direct Python reference runner.
- `python3 scripts/run_read_only.py`: direct local server entrypoint.
- `python3 -m unittest discover -s tests [-p PATTERN]`: direct test invocation.
- `cgi-bin/create_thread.py` and `cgi-bin/create_reply.py`: direct write-command entrypoints for lower-level testing and parity work.

## Runtime environment
- Repo-root `.env` is loaded automatically for the main local server path, direct WSGI import path, CGI write entrypoints, and `./forum test`.
- Run `./forum env-sync` after pulling changes that add new keys to `.env.example`.
- Restart the relevant process after changing `.env`.
- Explicit process environment variables still override `.env`.
- `FORUM_HOST` and `FORUM_PORT` control the local server bind address for `./forum start`.
- `DEDALUS_API_KEY` enables the server-side `/api/call_llm` baseline LLM endpoint.
- The wrapper prefers `.venv/bin/python3` when present and otherwise falls back to `python3`.

## Public instance info
- The public `/instance/` page publishes operator, policy, and deployment facts for the current instance.
- Tracked public metadata lives in `records/instance/public.txt`.
- Commit ID and commit date are derived from the current git checkout at render time.
- Moderation settings are derived from the current moderator allowlist configuration.

## Dedalus baseline
1. Install dependencies with `python3 -m pip install -r requirements.txt`.
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
