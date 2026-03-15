## Stage 1 - Supported host profile
- Changes:
  - Added [php_primary_host_installation.md](/home/wsl/v2/docs/php_primary_host_installation.md) defining the supported PHP-primary hosting profile, unsupported environments, canonical Python boundary, planned deployment layout, and the minimal PHP adapter contract.
- Verification:
  - Reviewed the documented host requirements against the current canonical entrypoints in `forum_read_only/web.py`, `cgi-bin/create_thread.py`, and `cgi-bin/create_reply.py`.
  - Confirmed the profile stays narrow: PHP front controller plus `.htaccess` for public routing, with Python remaining the canonical read/write implementation.
- Notes:
  - The remaining implementation work depends on picking one thin request-forwarding strategy that a typical Apache shared host can support without turning this into a PHP rewrite.
