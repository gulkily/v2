# v2

`v2` is a forum where every accepted post becomes a git commit. No database, no migrations, no schema drift: the repository is the forum state.

If you need a more descriptive handle than `v2`, think of it as a git-backed forum experiment aimed at cheap, PHP-primary hosting that can still run a little Python CGI.

## Why

Most forums hide their state behind an application database. This one keeps canonical records in the repo itself, then renders HTML pages and plain-text API responses from those files. The upside is a simple, inspectable state model with git history, diffs, and replication built in. The tradeoff is that writes are constrained by git and filesystem semantics rather than a traditional transactional database, so this is intentionally optimized for small deployments and builder-friendly experimentation, not high-write production scale.

## What It Does

- Serves forum pages and plain-text API responses from repository-backed records
- Accepts signed thread and reply submissions through canonical `/api/create_thread` and `/api/create_reply` endpoints
- Verifies detached OpenPGP signatures from the browser signing flow before accepting writes
- Stores accepted posts, signatures, and related records directly in the repo and creates git commits for them
- Supports a thin PHP adapter for Apache-style shared hosts that can still execute Python CGI

## What It Looks Like

The machine-readable surface is intentionally plain text:

```bash
$ curl http://127.0.0.1:8000/api/
FORUM-API/1
Mode: mixed
Available-Commands: list_index get_thread get_post get_profile get_moderation_log call_llm create_thread create_reply moderate link_identity update_profile
...
```

```bash
$ curl 'http://127.0.0.1:8000/api/list_index'
Command: list_index
Board-Tag: all
Entry-Count: <n>
...
```

## Signed Posting

 Browser posting is not session-token auth dressed up with new wording. The compose flow generates or loads an OpenPGP keypair in the browser, signs a canonical ASCII payload client-side, and submits `payload`, `signature`, and `public_key` to the write endpoint. The server verifies the detached signature, stores the accepted record plus its detached signature in the repo, and stores one canonical public-key file per signer fingerprint under `records/public-keys/` for reuse across later signed records.

## Local Setup

1. Install Python dependencies:

```bash
./forum install
```

If you prefer a repo-local virtual environment instead of a user-profile install, use `./forum install --target venv`.

2. Sync the repo-root environment file:

```bash
./forum env-sync
```

3. Start the local server:

```bash
./forum start
```

4. Open `http://127.0.0.1:8000/`.

## Common Commands

- `./forum help`
- `./forum install`
- `./forum env-sync`
- `./forum git-recover`
- `./forum content-purge records/posts`
- `./forum rebuild-index`
- `./forum php-host-refresh`
- `./forum start`
- `./forum test`

More command and runtime details are in [docs/developer_commands.md](docs/developer_commands.md).

## Operator Cleanup

For future clean-start resets, operators can archive and purge canonical content from reachable git history with `./forum content-purge ...`.

- Preview one or more record families with `./forum content-purge records/posts records/identity`.
- Apply the workflow only after reviewing the preview and choosing an archive target outside the repo, for example `./forum content-purge records/posts --apply --archive-output /tmp/forum-posts.zip`.
- Real apply mode requires `git-filter-repo`; the command looks on `PATH` first and then checks `$HOME/.local/bin/git-filter-repo` directly.
- If `git-filter-repo` is missing, the command suggests a no-sudo install path with `python3 -m pip install --user git-filter-repo`.
- After a purge removes `records/posts/` and related record families, new writes recreate the needed directories automatically, so signed posting can resume without manual directory repair.

## PHP Shim Refresh

If the PHP-primary frontend still shows stale threads after a history rewrite or large cleanup:

- Run `./forum php-host-refresh`.
- The refresh command now rebuilds the derived post index, refreshes PHP-native read artifacts, recreates the PHP microcache directory, and clears generated static HTML artifacts.
- If stale PHP-rendered reads still persist after `./forum php-host-refresh`, remove `state/php_host_cache/` entirely and let the adapter recreate it on the next request.
- If you only need the Python read path, `./forum rebuild-index` still rebuilds the derived index by itself.

## Deployment

- PHP-primary host deployment: [docs/php_primary_host_installation.md](docs/php_primary_host_installation.md)
- Source checkout: `https://github.com/gulkily/v2`

## Status

Early-stage experiment. The core model works, the edges are still rough, and PRs are welcome.

## Repo Layout

- [forum_web](forum_web): HTTP-facing WSGI application
- [forum_cgi](forum_cgi): shared CGI and write-path helpers
- [cgi-bin](cgi-bin): canonical CGI entrypoints
- [records](records): repository-backed forum state
- [docs](docs): operator, planning, and development docs

## License

See [LICENSE](LICENSE).
