## Stage 1 - shared read contract
- Changes:
  - Added the first shared cross-runtime read contract in [php_host_native_read_performance_shared_read_contract.md](/home/wsl/v2/docs/plans/php_host_native_read_performance_shared_read_contract.md).
  - Narrowed the v1 duplicated-path scope to one explicit route, `/`, with strict exclusions for query variants, personalized requests, and all write-sensitive paths.
  - Defined the Python-versus-PHP authority boundary, the prepared snapshot expectations, and the fallback/invalidation rules so later PHP-native work has a concrete spec.
- Verification:
  - Manual review against the approved Step 2 and Step 3 docs to confirm the contract stays within the planned allowlisted anonymous read boundary and leaves writes authoritative in Python.
- Notes:
  - This stage intentionally lands the spec first. No PHP-native rendering code is introduced until the shared contract is explicit enough to avoid accidental drift.
