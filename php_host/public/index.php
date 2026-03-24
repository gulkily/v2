<?php

declare(strict_types=1);

function forum_source_script_path(): string
{
    $resolved = realpath(__FILE__);
    if (is_string($resolved) && $resolved !== '') {
        return $resolved;
    }
    return __FILE__;
}

function forum_source_dir(): string
{
    return dirname(forum_source_script_path());
}

function forum_public_script_path(): string
{
    $scriptFilename = $_SERVER['SCRIPT_FILENAME'] ?? '';
    if (is_string($scriptFilename) && $scriptFilename !== '') {
        $resolved = realpath($scriptFilename);
        if (is_string($resolved) && $resolved !== '') {
            return $resolved;
        }
        if ($scriptFilename[0] === DIRECTORY_SEPARATOR) {
            return $scriptFilename;
        }
        $cwd = getcwd();
        if (is_string($cwd) && $cwd !== '') {
            return $cwd . DIRECTORY_SEPARATOR . $scriptFilename;
        }
        return $scriptFilename;
    }
    return __FILE__;
}

function forum_public_dir(): string
{
    return dirname(forum_public_script_path());
}

function forum_host_config_path(): string
{
    $publicConfig = forum_public_dir() . DIRECTORY_SEPARATOR . 'forum_host_config.php';
    if (is_file($publicConfig)) {
        return $publicConfig;
    }

    $sourceConfig = forum_source_dir() . DIRECTORY_SEPARATOR . 'forum_host_config.php';
    if (is_file($sourceConfig)) {
        return $sourceConfig;
    }

    return $publicConfig;
}

function forum_render_missing_config_page(string $path): never
{
    http_response_code(500);
    header('Content-Type: text/html; charset=utf-8');

    $title = 'PHP host setup required';
    $pathHtml = htmlspecialchars($path, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    $commandHtml = htmlspecialchars('./forum php-host-setup /absolute/path/to/public-web-root', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');

    echo <<<HTML
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{$title}</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f3ea;
      --panel: #fffdf8;
      --text: #1f1a14;
      --muted: #6f6252;
      --accent: #8a4b14;
      --accent-soft: #f3dfcb;
      --border: #d8c7b2;
      --code-bg: #f1ebe1;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top, #fff8ee 0, #f6f3ea 48%, #eee5d8 100%);
      color: var(--text);
      display: grid;
      place-items: center;
      padding: 24px;
    }
    main {
      width: min(760px, 100%);
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 20px;
      box-shadow: 0 24px 80px rgba(73, 43, 16, 0.12);
      overflow: hidden;
    }
    .hero {
      padding: 28px 28px 18px;
      background: linear-gradient(135deg, #fff6ea 0%, #f8ead8 100%);
      border-bottom: 1px solid var(--border);
    }
    .eyebrow {
      margin: 0 0 10px;
      font-size: 12px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--accent);
    }
    h1 {
      margin: 0 0 12px;
      font-size: clamp(32px, 5vw, 46px);
      line-height: 1.05;
    }
    .lede {
      margin: 0;
      font-size: 18px;
      line-height: 1.6;
      color: var(--muted);
    }
    .body {
      padding: 24px 28px 30px;
      display: grid;
      gap: 18px;
    }
    .card {
      padding: 18px;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: #fffdfa;
    }
    h2 {
      margin: 0 0 10px;
      font-size: 18px;
    }
    p, li {
      font-size: 16px;
      line-height: 1.6;
    }
    p { margin: 0; }
    ul {
      margin: 0;
      padding-left: 20px;
    }
    code, pre {
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
      font-size: 14px;
    }
    pre {
      margin: 0;
      padding: 14px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      border-radius: 12px;
      background: var(--code-bg);
      border: 1px solid var(--border);
    }
    .note {
      color: var(--muted);
    }
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">PHP Host Configuration</p>
      <h1>{$title}</h1>
      <p class="lede">This PHP adapter is installed, but the required host-local config include is missing, so the forum cannot start yet.</p>
    </section>
    <section class="body">
      <article class="card">
        <h2>What is missing</h2>
        <p>The adapter could not load <code>forum_host_config.php</code>.</p>
      </article>
      <article class="card">
        <h2>Expected path</h2>
        <pre>{$pathHtml}</pre>
      </article>
      <article class="card">
        <h2>Recommended recovery</h2>
        <p>From the application checkout, regenerate the PHP host config and publish the expected public files:</p>
        <pre>{$commandHtml}</pre>
      </article>
      <article class="card">
        <h2>Need more detail?</h2>
        <p>Open <code>docs/php_primary_host_installation.md</code> in the application checkout for the supported PHP-host installation flow and verification steps.</p>
      </article>
      <article class="card note">
        <h2>Why the site stops here</h2>
        <p>This page indicates a deployment/configuration problem, not a normal application error. The adapter fails closed until the required host-local config include is present.</p>
      </article>
    </section>
  </main>
</body>
</html>
HTML;
    exit;
}

function forum_host_config(): array
{
    static $config = null;
    if (is_array($config)) {
        return $config;
    }

    $path = forum_host_config_path();
    if (!is_file($path)) {
        forum_render_missing_config_page($path);
    }

    $loaded = require $path;
    if (!is_array($loaded)) {
        http_response_code(500);
        header('Content-Type: text/plain; charset=utf-8');
        echo "Invalid PHP host config include.\n";
        exit;
    }

    $config = $loaded;
    return $config;
}

require_once forum_source_dir() . '/cache.php';

function forum_app_root(): string
{
    $configured = forum_host_config()['app_root'] ?? '';
    if (is_string($configured) && $configured !== '') {
        return rtrim($configured, DIRECTORY_SEPARATOR);
    }

    $fallback = getenv('FORUM_PHP_APP_ROOT');
    if (is_string($fallback) && $fallback !== '') {
        return rtrim($fallback, DIRECTORY_SEPARATOR);
    }

    return dirname(forum_source_dir(), 2);
}

function forum_python_command(string $repoRoot): array
{
    $venvPython = $repoRoot . '/.venv/bin/python3';
    if (is_executable($venvPython)) {
        return [$venvPython, $repoRoot . '/cgi-bin/forum_web.py'];
    }

    return ['python3', $repoRoot . '/cgi-bin/forum_web.py'];
}

function forum_cgi_environment(): array
{
    $environment = $_ENV;
    $config = forum_host_config();
    foreach ($_SERVER as $key => $value) {
        if (is_string($value)) {
            $environment[$key] = $value;
        }
    }
    $headers = function_exists('getallheaders') ? getallheaders() : [];
    if ($headers === []) {
        foreach ($_SERVER as $key => $value) {
            if (!is_string($value) || strncmp($key, 'HTTP_', 5) !== 0) {
                continue;
            }
            $name = str_replace(' ', '-', ucwords(strtolower(str_replace('_', ' ', substr($key, 5)))));
            $headers[$name] = $value;
        }
    }
    foreach ($headers as $name => $value) {
        $httpName = 'HTTP_' . strtoupper(str_replace('-', '_', $name));
        $environment[$httpName] = $value;
    }
    $environment['PATH_INFO'] = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
    $environment['QUERY_STRING'] = $_SERVER['QUERY_STRING'] ?? '';
    $environment['REQUEST_METHOD'] = $_SERVER['REQUEST_METHOD'] ?? 'GET';
    $environment['CONTENT_TYPE'] = $_SERVER['CONTENT_TYPE'] ?? '';
    $environment['CONTENT_LENGTH'] = $_SERVER['CONTENT_LENGTH'] ?? '0';
    $environment['REQUEST_SCHEME'] = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
    $environment['REDIRECT_STATUS'] = '200';
    if (isset($config['repo_root']) && is_string($config['repo_root']) && $config['repo_root'] !== '') {
        $environment['FORUM_REPO_ROOT'] = $config['repo_root'];
    }
    if (isset($config['app_root']) && is_string($config['app_root']) && $config['app_root'] !== '') {
        $environment['FORUM_PHP_APP_ROOT'] = $config['app_root'];
    }
    return $environment;
}

function forum_parse_cgi_response(string $response): array
{
    [$rawHeaders, $body] = array_pad(preg_split("/\r?\n\r?\n/", $response, 2), 2, '');
    $statusCode = 200;
    $headers = [];
    foreach (preg_split("/\r?\n/", trim($rawHeaders)) as $line) {
        if ($line === '') {
            continue;
        }
        if (stripos($line, 'Status:') === 0) {
            $statusLine = trim(substr($line, 7));
            $statusCode = (int) strtok($statusLine, ' ');
            continue;
        }
        $headers[] = $line;
    }

    return [
        'status_code' => $statusCode,
        'headers' => $headers,
        'body' => $body,
    ];
}

function forum_apply_response_headers(array $headers): void
{
    foreach ($headers as $line) {
        header($line, false);
    }
}

function forum_header_value(array $headers, string $name): ?string
{
    $prefix = strtolower($name) . ':';
    foreach ($headers as $line) {
        if (!is_string($line)) {
            continue;
        }
        $trimmed = trim($line);
        if (strtolower(substr($trimmed, 0, strlen($prefix))) !== $prefix) {
            continue;
        }
        return trim(substr($trimmed, strlen($prefix)));
    }
    return null;
}

function forum_is_post_index_rebuild_status_response(array $parsed): bool
{
    return forum_header_value($parsed['headers'], 'X-Forum-Post-Index-Status') === 'required';
}

function forum_render_post_index_rebuild_status_page(string $targetPath, string $rebuildPath): string
{
    $title = htmlspecialchars('Refreshing the forum', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    $targetPathHtml = htmlspecialchars($targetPath, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    $rebuildPathHtml = htmlspecialchars($rebuildPath, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    $targetPathJson = json_encode($targetPath, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);
    $rebuildPathJson = json_encode($rebuildPath, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);

    return <<<HTML
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{$title}</title>
  <style>
    :root {
      color-scheme: light dark;
      --bg: #f3f1ea;
      --panel: #fbfaf5;
      --text: #1f2a28;
      --muted: #5f6b67;
      --accent: #2d5b73;
      --border: rgba(82, 101, 96, 0.18);
      --button-bg: #fffaf1;
      --button-border: rgba(82, 101, 96, 0.22);
      --shadow: rgba(31, 42, 40, 0.1);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: Verdana, Tahoma, Geneva, sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    .wrap {
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 1.5rem;
    }
    .card {
      width: min(38rem, 100%);
      background: var(--panel);
      border: 1px solid var(--border);
      box-shadow: 0 14px 34px var(--shadow);
      padding: 1.25rem 1.2rem;
      border-radius: 0.35rem;
    }
    .kicker {
      margin: 0 0 0.45rem;
      color: var(--accent);
      font: 0.78rem "Courier New", Courier, monospace;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    h1 {
      margin: 0.1rem 0 0.65rem;
      font: 2rem Georgia, "Times New Roman", serif;
    }
    p {
      margin: 0.55rem 0;
      line-height: 1.5;
    }
    .meta {
      color: var(--muted);
      font-size: 0.96rem;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.7rem;
      margin-top: 1rem;
    }
    .actions a {
      display: inline-block;
      padding: 0.5rem 0.75rem;
      border: 1px solid var(--button-border);
      color: var(--text);
      text-decoration: none;
      background: var(--button-bg);
    }
    iframe {
      width: 0;
      height: 0;
      border: 0;
      position: absolute;
      inset: auto;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #111820;
        --panel: #18212b;
        --text: #e4ece9;
        --muted: #b4c0bc;
        --accent: #8fc4df;
        --border: rgba(162, 184, 180, 0.22);
        --button-bg: #24313c;
        --button-border: rgba(162, 184, 180, 0.22);
        --shadow: rgba(0, 0, 0, 0.42);
      }
    }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="card">
      <p class="kicker">zenmemes</p>
      <h1>Refreshing the forum...</h1>
      <p>A small interval of stillness while the next page arrives.</p>
      <p class="meta">This page will continue in a moment.</p>
      <div class="actions">
        <a href="{$targetPathHtml}">retry now</a>
      </div>
    </section>
  </main>
  <iframe id="forum-reindex-worker" title="" aria-hidden="true" tabindex="-1"></iframe>
  <script>
    (function () {
      var targetPath = {$targetPathJson};
      var rebuildPath = {$rebuildPathJson};
      var worker = document.getElementById("forum-reindex-worker");
      var completed = false;
      function finish() {
        if (completed) {
          return;
        }
        completed = true;
        window.location.replace(targetPath);
      }
      worker.addEventListener("load", finish, { once: true });
      worker.src = rebuildPath;
    }());
  </script>
</body>
</html>
HTML;
}

function forum_apply_post_index_rebuild_status_response(array $parsed, array $extraHeaders = []): array
{
    $targetPath = forum_header_value($parsed['headers'], 'X-Forum-Post-Index-Target-Path') ?? '/';
    $rebuildPath = forum_header_value($parsed['headers'], 'X-Forum-Post-Index-Rebuild-Path') ?? $targetPath;
    http_response_code(200);
    forum_apply_response_headers([
        'Content-Type: text/html; charset=utf-8',
        'Cache-Control: no-store',
        'Vary: User-Agent',
    ]);
    forum_apply_response_headers($extraHeaders);
    echo forum_render_post_index_rebuild_status_page($targetPath, $rebuildPath);
    return $parsed;
}

function forum_apply_static_html_response(string $body, array $extraHeaders = []): void
{
    http_response_code(200);
    forum_apply_response_headers([
        'Content-Type: text/html; charset=utf-8',
    ]);
    forum_apply_response_headers($extraHeaders);
    echo $body;
}

function forum_apply_cgi_response(string $response, array $extraHeaders = []): array
{
    $parsed = forum_parse_cgi_response($response);
    $statusCode = (int) $parsed['status_code'];
    if ($statusCode === 0) {
        $statusCode = 500;
    }
    http_response_code($statusCode);
    forum_apply_response_headers($parsed['headers']);
    forum_apply_response_headers($extraHeaders);
    echo $parsed['body'];
    return $parsed;
}

function forum_input_stream()
{
    $input = fopen('php://input', 'rb');
    if ($input !== false && PHP_SAPI !== 'cli') {
        return $input;
    }
    if ($input !== false) {
        fclose($input);
    }
    return fopen('php://stdin', 'rb');
}

$staticHtml = forum_read_static_html();
if (is_string($staticHtml)) {
    forum_apply_static_html_response($staticHtml, ['X-Forum-Static-Html: HIT']);
    exit;
}

$cachedResponse = forum_read_cached_response();
if (is_string($cachedResponse)) {
    forum_apply_cgi_response($cachedResponse, array_merge(['X-Forum-Php-Cache: HIT'], forum_asset_cache_headers()));
    exit;
}

$appRoot = forum_app_root();
$command = forum_python_command($appRoot);
$descriptorSpec = [
    0 => ['pipe', 'r'],
    1 => ['pipe', 'w'],
    2 => ['pipe', 'w'],
];
$process = proc_open($command, $descriptorSpec, $pipes, $appRoot, forum_cgi_environment());

if (!is_resource($process)) {
    http_response_code(500);
    header('Content-Type: text/plain; charset=utf-8');
    echo "Failed to start forum CGI bridge.\n";
    exit;
}

$input = forum_input_stream();
if ($input !== false) {
    stream_copy_to_stream($input, $pipes[0]);
    fclose($input);
}
fclose($pipes[0]);

$stdout = stream_get_contents($pipes[1]);
$stderr = stream_get_contents($pipes[2]);
fclose($pipes[1]);
fclose($pipes[2]);

$exitCode = proc_close($process);
if ($exitCode !== 0) {
    http_response_code(500);
    header('Content-Type: text/plain; charset=utf-8');
    echo "Forum CGI bridge failed.\n";
    if ($stderr !== '') {
        echo $stderr;
    }
    exit;
}

$response = $stdout === false ? '' : $stdout;
$parsed = forum_parse_cgi_response($response);
if (forum_is_post_index_rebuild_status_response($parsed)) {
    forum_apply_post_index_rebuild_status_response($parsed, ['X-Forum-Php-Cache: MISS']);
    exit;
}
forum_store_static_html($parsed);
forum_store_cached_response($parsed, $response);
forum_apply_cgi_response($response, array_merge(['X-Forum-Php-Cache: MISS'], forum_asset_cache_headers()));
if (forum_mutating_request() && (int) $parsed['status_code'] >= 200 && (int) $parsed['status_code'] < 400) {
    forum_clear_cache();
    forum_clear_static_html();
}
