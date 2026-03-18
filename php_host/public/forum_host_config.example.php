<?php

declare(strict_types=1);

return [
    // Absolute path to the deployed application checkout that contains cgi-bin/ and forum code.
    'app_root' => '/absolute/path/to/v2',

    // Absolute path to the writable forum data repository root.
    'repo_root' => '/absolute/path/to/v2',

    // Absolute path to a writable directory for PHP microcache files.
    'cache_dir' => '/absolute/path/to/v2/state/php_host_cache',

    // Optional short TTL in seconds for allowlisted public read routes.
    'microcache_ttl' => 5,
];
