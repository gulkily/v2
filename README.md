# v2

`v2` is a git-backed forum prototype that treats the repository itself as the source of truth for forum state. It pairs a Python read surface with CGI-style write commands, browser-based signed posting flows, and a deployment profile for PHP-primary web hosts.

## What It Does
- Explores a forum model where accepted content is stored directly in git-backed records instead of a traditional database
- Serves forum pages and plain-text API responses from repository-backed records
- Accepts signed thread and reply submissions through canonical `/api/create_thread` and `/api/create_reply` endpoints
- Stores accepted writes directly in the repo and records git commits for them
- Supports a thin PHP adapter for Apache-style shared hosts that can still execute Python CGI

## Local Setup
1. Install Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

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
- `./forum env-sync`
- `./forum start`
- `./forum test` preferred test entrypoint
- `python3 -m unittest discover -s tests` direct equivalent if you want to bypass the wrapper

More command and runtime details are in [docs/developer_commands.md](docs/developer_commands.md).

## Deployment
- PHP-primary host deployment: [docs/php_primary_host_installation.md](docs/php_primary_host_installation.md)
- Source checkout: `https://github.com/gulkily/v2`

## Repo Layout
- [forum_web](forum_web): HTTP-facing WSGI application
- [forum_cgi](forum_cgi): shared CGI/write helpers
- [cgi-bin](cgi-bin): canonical CGI entrypoints
- [records](records): repository-backed forum state
- [docs](docs): operator, planning, and development docs

## License
See [LICENSE](LICENSE).
