# Compose Reply Latency Reduction Operator Checklist

- Warm the normal write path first by creating a representative thread through `/api/create_thread`, then load `/compose/reply?thread_id=<thread-id>&parent_id=<thread-id>`.
- Confirm the reply-compose request returns `X-Forum-Response-Source: php-native-compose-reply` and `X-Forum-Php-Native: HIT`.
- Confirm the page body includes the expected compose UI plus the visible reply-target reference block.
- Verify the identity-hint cookie path still stays on the native route by repeating the request with only `forum_identity_hint` present.
- Verify snapshot-missing fallback by temporarily deleting the matching `compose-reply/<thread-id>/<parent-id>` row from `state/cache/php_native_reads.sqlite3`; the next request should fall through with `X-Forum-Php-Native-Fallback: snapshot-missing`.
- After fallback verification, run the normal artifact refresh flow again so the compose-reply snapshot is restored.
