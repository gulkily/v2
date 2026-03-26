## PHP-Native Root Read Checklist

### Goal
- Verify that the PHP host can serve the allowlisted anonymous `/` route from the prepared snapshot without per-request Python CGI, while still falling back safely for out-of-scope requests.

### Before Deployment
- Confirm `state/cache/php_native_reads/board_index_root.json` exists in the deployed repo root after at least one successful content write.
- Confirm the PHP host `forum_host_config.php` points `repo_root` at the same repository checkout that receives content writes.
- Confirm `php_host/public/index.php` includes the PHP-native route handling and is deployed together with the Python snapshot refresh hook.

### Anonymous Root Read
- Request `/` with no query string, cookies, or authorization headers.
- Confirm the response is `200`.
- Confirm the response headers include `X-Forum-Php-Native: HIT`.
- Confirm the page contains visible thread links and the board stats panel.

### Fallback Boundaries
- Request `/?board_tag=meta`.
- Confirm the request does not return `X-Forum-Php-Native: HIT`.
- Confirm the page still renders through the existing PHP-to-Python path.
- Request a non-covered route such as `/threads/<post-id>`.
- Confirm existing static HTML or Python-backed behavior remains unchanged.

### Freshness After Writes
- Submit a new thread or other post write through the normal application path.
- Confirm `state/cache/php_native_reads/board_index_root.json` updates.
- Request `/` again and confirm the new thread appears without requiring a PHP-host refresh.

### Recovery
- Temporarily move or corrupt `board_index_root.json`.
- Request `/`.
- Confirm the request falls back cleanly rather than emitting partial native output.
