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

- Read requests are served by the current WSGI application in `forum_read_only/web.py`.
- Write requests continue to use the existing CGI command entrypoints in `cgi-bin/create_thread.py` and `cgi-bin/create_reply.py`.
- Browser posting continues to target `/api/create_thread` and `/api/create_reply`.

The PHP layer is only a thin adapter for host compatibility. It must not reimplement routing, rendering, payload validation, repository writes, or API response rules.

## Planned Public Layout
The supported installation shape assumes:

- a public web root containing `index.php`, `.htaccess`, and any public static assets
- a Python-accessible repository root outside or alongside the public web root
- a `cgi-bin` location for the canonical Python write commands
- the sample adapter artifacts in `php_host/public/` copied into the host's public web root
- the sample read bridge in `cgi-bin/forum_web.py` deployed with the rest of the repo

The exact file layout can vary by host, but the adapter contract stays fixed:

1. Apache routes non-static read requests through the PHP front controller.
2. The PHP front controller forwards the request into the canonical Python read surface.
3. Write requests continue to reach the canonical Python write commands without changing endpoint names or payload formats.

## Minimal Adapter Contract
The PHP adapter must do only the following:

- accept the incoming request method, path, query string, headers, and body
- map that request onto the canonical Python read or write surface
- return the Python-generated status, headers, and body unchanged except for host-required transport details

Any host-specific glue should stay inside the adapter and deployment docs, not spread into the forum logic.
