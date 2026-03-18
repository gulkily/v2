# PHP-Primary Host Installation Profile

## Supported Profile
This project supports one PHP-primary hosting profile: an Apache-style shared host that provides:

- PHP for the public web entrypoint
- `.htaccess` support with `mod_rewrite`
- Python 3 available for CGI execution
- a `cgi-bin` directory, or an equivalent way to execute Python CGI scripts
- read/write filesystem access for the deployed repository
- git available to the Python write commands

This profile is intentionally narrow. It is meant for PHP-first hosts that can still invoke the existing Python application surfaces. It is not a PHP-native version of the forum.

## Unsupported Environments
This profile does not cover:

- PHP-only hosts with no Python execution
- hosts with no CGI support and no way for PHP to invoke the existing Python entrypoints
- hosts that block repository writes or git execution
- hosts that require a different reverse-proxy or application-server model

## Canonical Application Boundary
The existing Python code remains canonical:

- Read requests are served by the current WSGI application in `forum_web/web.py`.
- Write requests continue to use the existing CGI command entrypoints in `cgi-bin/create_thread.py` and `cgi-bin/create_reply.py`.
- Browser posting continues to target `/api/create_thread` and `/api/create_reply`.

The PHP layer is only a thin adapter for host compatibility. It must not reimplement routing, rendering, payload validation, repository writes, or API response rules.

## PHP Microcache Boundary
The sample PHP adapter includes a short-lived file microcache for explicitly safe public `GET` routes. This cache is adapter-only:

- canonical rendering still comes from the Python read surface
- write endpoints remain uncached
- successful writes routed through the PHP shim clear cached public reads
- canonical static asset routes receive explicit cache headers

The adapter allowlist is intentionally narrow. It is meant for public read routes such as `/`, thread pages, post pages, `/instance/`, `/llms.txt`, and selected read APIs. Compose flows, signed submission flows, and request-context-sensitive behavior should not be added to the cache allowlist casually.

## Planned Public Layout
The supported installation shape assumes:

- a public web root containing symlinks or host-published copies of `index.php`, `.htaccess`, and `forum_host_config.php`
- a Python-accessible repository root outside or alongside the public web root
- a `cgi-bin` location for the canonical Python write commands
- the adapter artifacts in `php_host/public/` remaining repo-managed, with the real `forum_host_config.php` generated locally and ignored by git
- the sample read bridge in `cgi-bin/forum_web.py` deployed with the rest of the repo

The generated `forum_host_config.php` is the primary adapter settings surface for:

- `app_root`: the deployed application checkout path
- `repo_root`: the writable forum data repository root
- `cache_dir`: the writable PHP microcache directory
- `microcache_ttl`: the short allowlisted read-cache lifetime in seconds

`forum_host_config.example.php` is tracked as the shape reference, while the real `forum_host_config.php` stays ignored by git because it contains host-local paths.

The exact file layout can vary by host, but the adapter contract stays fixed:

1. Apache routes non-static read requests through the PHP front controller.
2. The PHP front controller forwards the request into the canonical Python surface.
3. Browser compose and API write requests continue to use `/api/create_thread` and `/api/create_reply` without changing payload formats or response shapes.

## Minimal Adapter Contract
The PHP adapter must do only the following:

- accept the incoming request method, path, query string, headers, and body
- map that request onto the canonical Python read or write surface
- return the Python-generated status, headers, and body unchanged except for host-required transport details

Any host-specific glue should stay inside the adapter and deployment docs, not spread into the forum logic.

## Installation Steps
1. Deploy the application checkout from `https://github.com/gulkily/v2` onto the host so the Python code, `cgi-bin/`, and `records/` tree remain available on disk.
2. If the host supports `git`, clone or update the checkout directly, for example `git clone https://github.com/gulkily/v2.git`.
3. Run `./forum php-host-setup /absolute/path/to/public-web-root` from the deployed checkout.
4. Accept the derived defaults or provide host-specific paths for the application checkout, forum data repository, and writable PHP cache directory when prompted.
5. Confirm the command generated `php_host/public/forum_host_config.php` and attempted to symlink `index.php`, `.htaccess`, and `forum_host_config.php` into the public web root.
6. If the host rejects symlinks, leave the generated config file in place and follow the command's manual copy or manual linking guidance for the three public files.
7. Ensure the host can execute `python3` and the deployed CGI scripts, and that git commands are permitted for write operations.
8. Confirm the deployed repository directories are writable anywhere the application stores records, signatures, generated keys, or identity bootstrap files.
9. If you need a non-default cache path or TTL, edit the generated `forum_host_config.php` rather than hand-editing `index.php`.

## Adapter Config File
- `php_host/public/forum_host_config.example.php`: tracked example showing the required config keys and file shape.
- `php_host/public/forum_host_config.php`: generated real config include; ignored by git; intended to be refreshed by `./forum php-host-setup`.
- The PHP adapter still tolerates narrowly scoped environment fallbacks for compatibility, but generated config is the primary supported operator path.

## Post-Install Checks
- Request `/` and confirm the board index renders through the PHP front controller.
- Confirm the public web root contains `index.php`, `.htaccess`, and `forum_host_config.php` as symlinks into the repo checkout when the host allows symlinks.
- Request `/` twice in quick succession and confirm the second response is served from the PHP cache layer, for example by checking the adapter's `X-Forum-Php-Cache` response header for `HIT`.
- Request `/threads/<existing-thread-id>` and confirm a thread page renders.
- Request `/assets/site.css` and confirm the canonical asset path still resolves.
- Confirm `/assets/site.css` includes an explicit `Cache-Control` header.
- Open `/compose/thread` and confirm the page still targets `/api/create_thread`.
- Submit one signed thread and one signed reply, then confirm git commits and stored record files appear in the forum repository.
- After a successful write through the PHP-hosted path, request `/` or the affected thread again and confirm the adapter serves a fresh response rather than a stale cached copy.
