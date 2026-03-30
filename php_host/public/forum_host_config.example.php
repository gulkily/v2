<?php

declare(strict_types=1);

return [
    // Absolute path to the published public web root that receives index.php, .htaccess, and forum_host_config.php.
    'public_web_root' => '/absolute/path/to/public-web-root',

    // Absolute path to the deployed application checkout that contains cgi-bin/ and forum code.
    'app_root' => '/absolute/path/to/v2',

    // Absolute path to the writable forum data repository root.
    'repo_root' => '/absolute/path/to/v2',

    // Absolute path to a writable directory for PHP microcache files.
    'cache_dir' => '/absolute/path/to/v2/state/php_host_cache',

    // Absolute path under the public web root for generated static HTML artifacts.
    'static_html_dir' => '/absolute/path/to/public-web-root/_static_html',

    // Optional shared site title for PHP-rendered public pages such as the anonymous board index.
    'site_title' => 'Forum Reader',

    // Optional short TTL in seconds for allowlisted public read routes.
    'microcache_ttl' => 5,
];
