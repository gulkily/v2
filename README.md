# v2

`v2` is a git-backed forum prototype with a Python read surface, CGI-style write commands, browser-based signed posting flows, and a deployment profile for PHP-primary web hosts.

## What It Does
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
- `./forum test`
- `python3 -m unittest discover -s tests`

More command and runtime details are in [docs/developer_commands.md](/home/wsl/v2/docs/developer_commands.md).

## Deployment
- PHP-primary host deployment: [docs/php_primary_host_installation.md](/home/wsl/v2/docs/php_primary_host_installation.md)
- Source checkout: `https://github.com/gulkily/v2`

## Repo Layout
- [forum_read_only](/home/wsl/v2/forum_read_only): read-side WSGI application
- [forum_cgi](/home/wsl/v2/forum_cgi): shared CGI/write helpers
- [cgi-bin](/home/wsl/v2/cgi-bin): canonical CGI entrypoints
- [records](/home/wsl/v2/records): repository-backed forum state
- [docs](/home/wsl/v2/docs): operator, planning, and development docs

## License
See [LICENSE](/home/wsl/v2/LICENSE).
