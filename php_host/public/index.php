<?php

declare(strict_types=1);

const FORUM_PRIMARY_NAV_SECTION_HOME = 'home';

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

function forum_elapsed_ms(float $startedAt): string
{
    return number_format((microtime(true) - $startedAt) * 1000.0, 2, '.', '');
}

function forum_timing_headers(
    float $requestStartedAt,
    string $responseSource,
    ?float $cgiStartedAt = null
): array {
    $headers = [
        'X-Forum-Response-Source: ' . $responseSource,
        'X-Forum-Request-Duration-Ms: ' . forum_elapsed_ms($requestStartedAt),
    ];
    if ($cgiStartedAt !== null) {
        $headers[] = 'X-Forum-Cgi-Duration-Ms: ' . forum_elapsed_ms($cgiStartedAt);
    }
    return $headers;
}

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

function forum_env_flag_enabled(string $name): bool
{
    $value = getenv($name);
    if (!is_string($value) || $value === '') {
        return false;
    }
    return in_array(strtolower(trim($value)), ['1', 'true', 'yes', 'on'], true);
}

function forum_html_escape(string $text): string
{
    return htmlspecialchars($text, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function forum_site_title(): string
{
    $configured = forum_host_config()['site_title'] ?? '';
    if (is_string($configured)) {
        $configured = trim($configured);
        if ($configured !== '') {
            return $configured;
        }
    }
    $configured = getenv('FORUM_SITE_TITLE');
    if (is_string($configured)) {
        $configured = trim($configured);
        if ($configured !== '') {
            return $configured;
        }
    }
    return 'Forum Reader';
}

function forum_php_native_board_index_route(): ?string
{
    if (forum_request_method() !== 'GET') {
        return null;
    }
    if (forum_post_index_rebuild_request()) {
        return null;
    }
    if (forum_request_query_string() !== '') {
        return null;
    }
    if (forum_request_has_cache_busting_credentials('/')) {
        return null;
    }
    if (forum_request_path() !== '/') {
        return null;
    }
    return 'board_index_root';
}

function forum_php_native_thread_route(): ?string
{
    if (forum_request_method() !== 'GET') {
        return null;
    }
    if (forum_post_index_rebuild_request()) {
        return null;
    }
    if (forum_request_query_string() !== '') {
        return null;
    }
    $path = forum_request_path();
    if (forum_request_has_cache_busting_credentials($path)) {
        return null;
    }
    if (!str_starts_with($path, '/threads/')) {
        return null;
    }
    if (str_ends_with($path, '/title')) {
        return null;
    }
    $threadId = trim(substr($path, strlen('/threads/')), '/');
    if ($threadId === '' || str_contains($threadId, '/')) {
        return null;
    }
    return $threadId;
}

function forum_php_native_profile_route(): ?string
{
    if (forum_request_method() !== 'GET') {
        return null;
    }
    if (forum_post_index_rebuild_request()) {
        return null;
    }
    if (forum_request_query_string() !== '') {
        return null;
    }
    $path = forum_request_path();
    if (forum_request_has_cache_busting_credentials($path)) {
        return null;
    }
    if (!str_starts_with($path, '/profiles/')) {
        return null;
    }
    if (str_contains($path, '/update') || str_contains($path, '/merge')) {
        return null;
    }
    $profileSlug = trim(substr($path, strlen('/profiles/')), '/');
    if ($profileSlug === '' || str_contains($profileSlug, '/')) {
        return null;
    }
    return $profileSlug;
}

function forum_repo_root(): string
{
    $configured = forum_host_config()['repo_root'] ?? '';
    if (is_string($configured) && $configured !== '') {
        return rtrim($configured, DIRECTORY_SEPARATOR);
    }
    $fallback = getenv('FORUM_REPO_ROOT');
    if (is_string($fallback) && $fallback !== '') {
        return rtrim($fallback, DIRECTORY_SEPARATOR);
    }
    return forum_app_root();
}

function forum_php_native_snapshot_path(string $routeName): ?string
{
    if ($routeName !== 'board_index_root') {
        return null;
    }
    return forum_repo_root() . DIRECTORY_SEPARATOR . 'state' . DIRECTORY_SEPARATOR . 'cache' . DIRECTORY_SEPARATOR . 'php_native_reads' . DIRECTORY_SEPARATOR . 'board_index_root.json';
}

function forum_php_native_db_path(): string
{
    return forum_repo_root() . DIRECTORY_SEPARATOR . 'state' . DIRECTORY_SEPARATOR . 'cache' . DIRECTORY_SEPARATOR . 'php_native_reads.sqlite3';
}

function forum_php_native_open_db(): ?SQLite3
{
    if (!class_exists('SQLite3')) {
        return null;
    }
    $path = forum_php_native_db_path();
    if (!is_file($path)) {
        return null;
    }
    try {
        $db = new SQLite3($path, SQLITE3_OPEN_READWRITE);
    } catch (Throwable $_error) {
        return null;
    }
    return $db;
}

function forum_php_native_load_snapshot(string $routeName): ?array
{
    $path = forum_php_native_snapshot_path($routeName);
    if (!is_string($path) || $path === '' || !is_file($path)) {
        return null;
    }
    $raw = @file_get_contents($path);
    if (!is_string($raw) || $raw === '') {
        return null;
    }
    $decoded = json_decode($raw, true);
    if (!is_array($decoded)) {
        return null;
    }
    if (($decoded['route'] ?? null) !== '/') {
        return null;
    }
    if (!isset($decoded['thread_rows']) || !is_array($decoded['thread_rows'])) {
        return null;
    }
    if (!isset($decoded['stats']) || !is_array($decoded['stats'])) {
        return null;
    }
    return $decoded;
}

function forum_php_native_increment_counter(string $routePath, string $userType, string $outcome): void
{
    $db = forum_php_native_open_db();
    if (!($db instanceof SQLite3)) {
        return;
    }
    $statement = $db->prepare(
        'INSERT INTO php_native_read_counters(route_path, user_type, outcome, count, updated_at) '
        . 'VALUES (:route_path, :user_type, :outcome, 1, :updated_at) '
        . 'ON CONFLICT(route_path, user_type, outcome) DO UPDATE SET count = count + 1, updated_at = excluded.updated_at'
    );
    if (!($statement instanceof SQLite3Stmt)) {
        $db->close();
        return;
    }
    $statement->bindValue(':route_path', $routePath, SQLITE3_TEXT);
    $statement->bindValue(':user_type', $userType, SQLITE3_TEXT);
    $statement->bindValue(':outcome', $outcome, SQLITE3_TEXT);
    $statement->bindValue(':updated_at', gmdate('c'), SQLITE3_TEXT);
    $statement->execute();
    $statement->close();
    $db->close();
}

function forum_php_native_load_thread_snapshot(string $threadId): ?array
{
    $db = forum_php_native_open_db();
    if (!($db instanceof SQLite3)) {
        return null;
    }
    $statement = $db->prepare('SELECT snapshot_json FROM php_native_snapshots WHERE snapshot_id = :snapshot_id');
    if (!($statement instanceof SQLite3Stmt)) {
        $db->close();
        return null;
    }
    $statement->bindValue(':snapshot_id', 'thread/' . $threadId, SQLITE3_TEXT);
    $result = $statement->execute();
    if (!($result instanceof SQLite3Result)) {
        $statement->close();
        $db->close();
        return null;
    }
    $row = $result->fetchArray(SQLITE3_ASSOC);
    $result->finalize();
    $statement->close();
    $db->close();
    if (!is_array($row) || !isset($row['snapshot_json']) || !is_string($row['snapshot_json'])) {
        return null;
    }
    $decoded = json_decode($row['snapshot_json'], true);
    if (!is_array($decoded)) {
        return null;
    }
    if (($decoded['route'] ?? null) !== '/threads/' . $threadId) {
        return null;
    }
    if (!isset($decoded['content_html']) || !is_string($decoded['content_html'])) {
        return null;
    }
    return $decoded;
}

function forum_php_native_load_profile_snapshot(string $profileSlug): ?array
{
    $db = forum_php_native_open_db();
    if (!($db instanceof SQLite3)) {
        return null;
    }
    $statement = $db->prepare('SELECT snapshot_json FROM php_native_snapshots WHERE snapshot_id = :snapshot_id');
    if (!($statement instanceof SQLite3Stmt)) {
        $db->close();
        return null;
    }
    $statement->bindValue(':snapshot_id', 'profile/' . $profileSlug, SQLITE3_TEXT);
    $result = $statement->execute();
    if (!($result instanceof SQLite3Result)) {
        $statement->close();
        $db->close();
        return null;
    }
    $row = $result->fetchArray(SQLITE3_ASSOC);
    $result->finalize();
    $statement->close();
    $db->close();
    if (!is_array($row) || !isset($row['snapshot_json']) || !is_string($row['snapshot_json'])) {
        return null;
    }
    $decoded = json_decode($row['snapshot_json'], true);
    if (!is_array($decoded)) {
        return null;
    }
    if (($decoded['route'] ?? null) !== '/profiles/' . $profileSlug) {
        return null;
    }
    if (!isset($decoded['content_html']) || !is_string($decoded['content_html'])) {
        return null;
    }
    return $decoded;
}

function forum_render_primary_nav(?string $activeSection = null): string
{
    $shell = forum_page_shell_content();
    $links = $shell['primary_nav'] ?? [];
    $mergeEnabled = forum_env_flag_enabled('FORUM_ENABLE_ACCOUNT_MERGE') ? '1' : '0';
    $items = [];
    foreach ($links as $link) {
        if (!is_array($link)) {
            continue;
        }
        $section = (string) ($link['section'] ?? '');
        $href = forum_html_escape((string) ($link['href'] ?? ''));
        $label = forum_html_escape((string) ($link['label'] ?? ''));
        $activeAttribute = ($section !== '' && $section === $activeSection) ? ' aria-current="page"' : '';
        $items[] = '  <a href="' . $href . '"' . $activeAttribute . '>' . $label . '</a>';
    }
    $items[] = '  <a href="" data-profile-nav-link data-profile-nav-state="unresolved" data-merge-feature-enabled="' . $mergeEnabled . '" aria-disabled="true" tabindex="-1">My profile</a>';
    return "<nav class=\"site-header-nav\" aria-label=\"Primary\">\n" . implode("\n", $items) . "\n</nav>";
}

function forum_render_page_header(?string $activeSection = null): string
{
    $shell = forum_page_shell_content();
    $headerTitle = forum_html_escape(forum_site_title());
    $tagline = forum_html_escape((string) ($shell['site_tagline'] ?? ''));
    $navHtml = forum_render_primary_nav($activeSection);
    return <<<HTML
<header class="site-header site-header--page">
  <div class="site-header-main">
    <div class="site-header-lockup">
      <p class="site-header-mark">(*)</p>
      <div class="site-header-copy">
        <p class="site-header-title"><a href="/">{$headerTitle}</a></p>
        <p class="site-header-tagline">{$tagline}</p>
      </div>
    </div>
    {$navHtml}
  </div>
</header>
HTML;
}

function forum_render_username_claim_cta(): string
{
    $shell = forum_page_shell_content();
    $claim = is_array($shell['username_claim'] ?? null) ? $shell['username_claim'] : [];
    $kicker = forum_html_escape((string) ($claim['kicker'] ?? 'Account setup'));
    $text = forum_html_escape((string) ($claim['text'] ?? ''));
    $actionLabel = forum_html_escape((string) ($claim['action_label'] ?? 'Choose your username'));
    return <<<HTML
<section class="site-username-claim panel" data-username-claim-cta>
  <div class="site-username-claim-copy">
    <p class="site-username-claim-kicker">{$kicker}</p>
    <p class="site-username-claim-text">{$text}</p>
  </div>
  <a class="thread-chip site-username-claim-link" data-username-claim-link href="">{$actionLabel}</a>
</section>
<script>
(function () {
  var root = document.querySelector('[data-username-claim-cta]');
  if (!root) { return; }
  var link = root.querySelector('[data-username-claim-link]');
  if (!link) { return; }
  var htmlRoot = document.documentElement;
  var href = htmlRoot.getAttribute('data-username-claim-href') || '';
  link.setAttribute('href', href);
}());
</script>
HTML;
}

function forum_render_page_footer(): string
{
    $shell = forum_page_shell_content();
    $lines = $shell['footer_lines'] ?? [];
    $items = [];
    foreach ($lines as $line) {
        $items[] = '    <p>' . forum_html_escape((string) $line) . '</p>';
    }
    return "<footer class=\"site-footer\">\n  <div class=\"site-footer-inner\">\n" . implode("\n", $items) . "\n  </div>\n</footer>";
}

function forum_render_feed_head_link_html(string $feedHref): string
{
    if ($feedHref === '') {
        return '';
    }
    $href = forum_html_escape($feedHref);
    return '<link rel="alternate" type="application/rss+xml" title="RSS feed" href="' . $href . '">';
}

function forum_render_page_scripts_html(bool $includeUsernameClaimScript = true): string
{
    $shell = forum_page_shell_content();
    $scripts = [];
    foreach (($shell['shared_script_sources'] ?? []) as $source) {
        $scripts[] = '<script type="module" src="' . forum_html_escape((string) $source) . '"></script>';
    }
    if ($includeUsernameClaimScript) {
        $scripts[] = '<script type="module" src="' . forum_html_escape((string) ($shell['username_claim_script_source'] ?? '/assets/username_claim_cta.js')) . '"></script>';
    }
    return implode("\n", $scripts);
}

function forum_page_shell_content(): array
{
    static $cached = null;
    if (is_array($cached)) {
        return $cached;
    }

    $paths = [
        forum_app_root() . '/templates/page_shell_content.json',
        dirname(forum_source_dir(), 2) . '/templates/page_shell_content.json',
    ];
    foreach (array_unique($paths) as $path) {
        $raw = @file_get_contents($path);
        if (!is_string($raw) || $raw === '') {
            continue;
        }
        $decoded = json_decode($raw, true);
        if (is_array($decoded)) {
            $cached = $decoded;
            return $cached;
        }
    }

    $cached = [];
    return $cached;
}

function forum_render_php_native_page(string $title, string $contentHtml, string $headExtrasHtml = '', ?string $activeSection = null): string
{
    $documentTitle = forum_html_escape($title);
    $usernameClaimBootstrap = forum_render_username_claim_bootstrap();
    $rawUsernameClaim = getenv('FORUM_ENABLE_USERNAME_CLAIM_CTA');
    $usernameClaimEnabled = !is_string($rawUsernameClaim) || $rawUsernameClaim === '' || forum_env_flag_enabled('FORUM_ENABLE_USERNAME_CLAIM_CTA');
    $usernameClaimHtml = $usernameClaimEnabled ? forum_render_username_claim_cta() : '';
    $headerHtml = forum_render_page_header($activeSection);
    $footerHtml = forum_render_page_footer();
    $scriptsHtml = forum_render_page_scripts_html($usernameClaimEnabled);
    return <<<HTML
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{$documentTitle}</title>
  <link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="shortcut icon" href="/favicon.ico">
  <link rel="stylesheet" href="/assets/site.css">
  {$usernameClaimBootstrap}
  {$headExtrasHtml}
</head>
<body>
  <div class="page-shell ">
    {$usernameClaimHtml}
    {$headerHtml}
    <main class="content-shell">
      {$contentHtml}
    </main>
    {$footerHtml}
  </div>
  {$scriptsHtml}
</body>
</html>
HTML;
}

function forum_render_username_claim_bootstrap(): string
{
    return <<<HTML
<script>
(function () {
  var htmlRoot = document.documentElement;
  htmlRoot.setAttribute('data-username-claim-visible', '0');
  htmlRoot.setAttribute('data-username-claim-href', '');
}());
</script>
HTML;
}

function forum_render_board_index_stats_html(array $stats): string
{
    $postCount = (int) ($stats['post_count'] ?? 0);
    $threadCount = (int) ($stats['thread_count'] ?? 0);
    $boardTagCount = (int) ($stats['board_tag_count'] ?? 0);
    return <<<HTML
<div class="stat-grid">
  <article class="stat-card"><span class="stat-number">{$postCount}</span><span class="stat-label">posts loaded</span></article>
  <article class="stat-card"><span class="stat-number">{$threadCount}</span><span class="stat-label">visible threads</span></article>
  <article class="stat-card"><span class="stat-number">{$boardTagCount}</span><span class="stat-label">board tags</span></article>
</div>
HTML;
}

function forum_parse_timestamp_epoch(string $rawValue): ?int
{
    $normalized = trim($rawValue);
    if ($normalized === '') {
        return null;
    }
    $timestamp = strtotime($normalized);
    if ($timestamp === false) {
        return null;
    }
    return (int) $timestamp;
}

function forum_format_exact_timestamp(int $timestamp): string
{
    return gmdate('F d, Y · H:i:s \U\T\C', $timestamp);
}

function forum_format_relative_timestamp(int $timestamp, ?int $nowTimestamp = null): string
{
    $now = $nowTimestamp ?? time();
    $seconds = $now - $timestamp;
    if (abs($seconds) < 5) {
        return 'just now';
    }
    $future = $seconds < 0;
    $seconds = abs($seconds);
    $units = [
        [365 * 24 * 60 * 60, 'year'],
        [30 * 24 * 60 * 60, 'month'],
        [7 * 24 * 60 * 60, 'week'],
        [24 * 60 * 60, 'day'],
        [60 * 60, 'hour'],
        [60, 'minute'],
        [1, 'second'],
    ];
    $unitSeconds = 1;
    $unitName = 'second';
    foreach ($units as [$candidateSeconds, $candidateName]) {
        if ($seconds >= $candidateSeconds) {
            $unitSeconds = $candidateSeconds;
            $unitName = $candidateName;
            break;
        }
    }
    $quantity = max(1, intdiv($seconds, $unitSeconds));
    $label = $quantity === 1 ? $unitName : $unitName . 's';
    if ($future) {
        return 'in ' . $quantity . ' ' . $label;
    }
    return $quantity . ' ' . $label . ' ago';
}

function forum_render_timestamp_html(string $rawValue, string $cssClass): string
{
    $timestamp = forum_parse_timestamp_epoch($rawValue);
    if ($timestamp === null) {
        return '';
    }
    $classHtml = forum_html_escape($cssClass);
    $titleHtml = forum_html_escape(forum_format_exact_timestamp($timestamp));
    $labelHtml = forum_html_escape(forum_format_relative_timestamp($timestamp));
    return '<span class="' . $classHtml . '" title="' . $titleHtml . '">' . $labelHtml . '</span>';
}

function forum_render_board_index_thread_row_html(int $rank, array $threadRow): string
{
    $subject = trim((string) ($threadRow['subject'] ?? ''));
    if ($subject === '') {
        $subject = 'Untitled thread';
    }
    $threadHref = (string) ($threadRow['thread_href'] ?? '');
    if ($threadHref === '') {
        $postId = trim((string) ($threadRow['post_id'] ?? ''));
        $threadHref = '/threads/' . $postId;
    }
    $preview = trim((string) ($threadRow['preview'] ?? ''));
    $tags = [];
    foreach (($threadRow['tags'] ?? []) as $tag) {
        if (!is_string($tag) || trim($tag) === '') {
            continue;
        }
        $tags[] = '[' . forum_html_escape(trim($tag)) . ']';
    }
    $replyCount = (int) ($threadRow['reply_count'] ?? 0);
    $threadType = trim((string) ($threadRow['thread_type'] ?? ''));
    $metaParts = [];
    if ($replyCount > 0) {
        $metaParts[] = $replyCount . ' repl' . ($replyCount === 1 ? 'y' : 'ies');
    }
    if ($threadType !== '') {
        $metaParts[] = forum_html_escape($threadType);
    }
    $lastActivityAt = trim((string) ($threadRow['last_activity_at'] ?? ''));
    if ($lastActivityAt !== '') {
        $timestampHtml = forum_render_timestamp_html($lastActivityAt, 'friendly-timestamp');
        if ($timestampHtml !== '') {
            $metaParts[] = 'last active ' . $timestampHtml;
        }
    }
    $tagsLineHtml = '';
    if ($tags !== []) {
        $tagsText = implode(' ', $tags);
        $tagsLineHtml = '<p class="board-index-thread-tags">' . $tagsText . '</p>';
    }
    $previewHtml = '';
    if ($preview !== '' && $preview !== $subject) {
        $previewHtml = '<p>' . forum_html_escape($preview) . '</p>';
    }
    $metaHtml = '';
    if ($metaParts !== []) {
        $metaHtml = '<p class="thread-meta">' . implode(' · ', $metaParts) . '</p>';
    }
    $rankHtml = forum_html_escape((string) $rank);
    $subjectHtml = forum_html_escape($subject);
    $threadHrefHtml = forum_html_escape($threadHref);
    return <<<HTML
<article class="board-index-thread-row">
  <p class="board-index-thread-rank">{$rankHtml}.</p>
  <div class="board-index-thread-main">
    <h3><a href="{$threadHrefHtml}">{$subjectHtml}</a></h3>
    {$tagsLineHtml}
    {$previewHtml}
    {$metaHtml}
  </div>
</article>
HTML;
}

function forum_render_board_index_thread_rows_html(array $threadRows): string
{
    $rows = [];
    $rank = 1;
    foreach ($threadRows as $threadRow) {
        if (!is_array($threadRow)) {
            continue;
        }
        $rows[] = forum_render_board_index_thread_row_html($rank, $threadRow);
        $rank += 1;
    }
    return implode("\n", $rows);
}

function forum_render_php_native_board_index_page(array $snapshot): string
{
    $threadRowsHtml = forum_render_board_index_thread_rows_html($snapshot['thread_rows']);
    $statsHtml = forum_render_board_index_stats_html($snapshot['stats']);
    $contentHtml = <<<HTML
<section class="panel page-section">
  <section class="board-index-thread-list" aria-label="Visible threads">
    {$threadRowsHtml}
  </section>
</section>
<section class="panel page-section">
  {$statsHtml}
</section>
HTML;
    return forum_render_php_native_page(
        forum_site_title(),
        $contentHtml,
        forum_render_feed_head_link_html('/?format=rss'),
        FORUM_PRIMARY_NAV_SECTION_HOME,
    );
}

function forum_render_php_native_thread_page(array $snapshot): string
{
    $title = trim((string) ($snapshot['title'] ?? ''));
    if ($title === '') {
        $title = trim((string) ($snapshot['thread_id'] ?? ''));
    }
    $contentHtml = (string) ($snapshot['content_html'] ?? '');
    $feedHref = trim((string) ($snapshot['feed_href'] ?? ''));
    return forum_render_php_native_page(
        $title,
        $contentHtml,
        forum_render_feed_head_link_html($feedHref),
        FORUM_PRIMARY_NAV_SECTION_HOME,
    );
}

function forum_read_php_native_board_index_response(): ?array
{
    $routeName = forum_php_native_board_index_route();
    if ($routeName === null) {
        return null;
    }
    $snapshot = forum_php_native_load_snapshot($routeName);
    if ($snapshot === null) {
        return null;
    }
    return [
        'status_code' => 200,
        'headers' => [
            'Content-Type: text/html; charset=utf-8',
        ],
        'body' => forum_render_php_native_board_index_page($snapshot),
    ];
}

function forum_read_php_native_thread_response(): array
{
    $threadId = forum_php_native_thread_route();
    if ($threadId === null) {
        return [
            'response' => null,
            'headers' => [],
        ];
    }
    $snapshot = forum_php_native_load_thread_snapshot($threadId);
    if ($snapshot === null) {
        $routePath = '/threads/' . $threadId;
        forum_php_native_increment_counter($routePath, 'anonymous', 'snapshot_missing');
        return [
            'response' => null,
            'headers' => ['X-Forum-Php-Native-Fallback: snapshot-missing'],
        ];
    }
    forum_php_native_increment_counter('/threads/' . $threadId, 'anonymous', 'native_hit');
    return [
        'response' => [
            'status_code' => 200,
            'headers' => [
                'Content-Type: text/html; charset=utf-8',
            ],
            'body' => forum_render_php_native_thread_page($snapshot),
        ],
        'headers' => [],
    ];
}

function forum_apply_native_response(array $parsed, array $extraHeaders = []): void
{
    http_response_code((int) ($parsed['status_code'] ?? 200));
    forum_apply_response_headers($parsed['headers'] ?? []);
    forum_apply_response_headers($extraHeaders);
    echo (string) ($parsed['body'] ?? '');
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

$forumRequestStartedAt = microtime(true);

$nativeResponse = forum_read_php_native_board_index_response();
if (is_array($nativeResponse)) {
    forum_apply_native_response($nativeResponse, array_merge(
        ['X-Forum-Php-Native: HIT'],
        forum_timing_headers($forumRequestStartedAt, 'php-native-board-index')
    ));
    exit;
}

$staticHtml = forum_read_static_html();
if (is_string($staticHtml)) {
    forum_apply_static_html_response($staticHtml, array_merge(
        ['X-Forum-Static-Html: HIT'],
        forum_timing_headers($forumRequestStartedAt, 'static-html')
    ));
    exit;
}

$threadNativeAttempt = forum_read_php_native_thread_response();
if (is_array($threadNativeAttempt['response'] ?? null)) {
    forum_apply_native_response($threadNativeAttempt['response'], array_merge(
        ['X-Forum-Php-Native: HIT'],
        forum_timing_headers($forumRequestStartedAt, 'php-native-thread')
    ));
    exit;
}
$threadFallbackHeaders = is_array($threadNativeAttempt['headers'] ?? null) ? $threadNativeAttempt['headers'] : [];

$profileSlug = forum_php_native_profile_route();
if (is_string($profileSlug) && $profileSlug !== '') {
    $profileSnapshot = forum_php_native_load_profile_snapshot($profileSlug);
    if (is_array($profileSnapshot)) {
        forum_apply_native_response(
            [
                'status_code' => 200,
                'headers' => [
                    'Content-Type: text/html; charset=utf-8',
                ],
                'body' => (string) $profileSnapshot['content_html'],
            ],
            array_merge(
                ['X-Forum-Php-Native: HIT'],
                forum_timing_headers($forumRequestStartedAt, 'php-native-profile')
            )
        );
        exit;
    }
}

$cachedResponse = forum_read_cached_response();
if (is_string($cachedResponse)) {
    forum_apply_cgi_response($cachedResponse, array_merge(
        ['X-Forum-Php-Cache: HIT'],
        $threadFallbackHeaders,
        forum_asset_cache_headers(),
        forum_timing_headers($forumRequestStartedAt, 'php-microcache')
    ));
    exit;
}

$appRoot = forum_app_root();
$command = forum_python_command($appRoot);
$cgiStartedAt = microtime(true);
$descriptorSpec = [
    0 => ['pipe', 'r'],
    1 => ['pipe', 'w'],
    2 => ['pipe', 'w'],
];
$process = proc_open($command, $descriptorSpec, $pipes, $appRoot, forum_cgi_environment());

if (!is_resource($process)) {
    http_response_code(500);
    header('Content-Type: text/plain; charset=utf-8');
    forum_apply_response_headers($threadFallbackHeaders);
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
    forum_apply_response_headers($threadFallbackHeaders);
    echo "Forum CGI bridge failed.\n";
    if ($stderr !== '') {
        echo $stderr;
    }
    exit;
}

$response = $stdout === false ? '' : $stdout;
$parsed = forum_parse_cgi_response($response);
if (forum_is_post_index_rebuild_status_response($parsed)) {
    forum_apply_post_index_rebuild_status_response($parsed, array_merge(
        ['X-Forum-Php-Cache: MISS'],
        $threadFallbackHeaders,
        forum_timing_headers($forumRequestStartedAt, 'cgi', $cgiStartedAt)
    ));
    exit;
}
forum_store_static_html($parsed);
forum_store_cached_response($parsed, $response);
forum_apply_cgi_response($response, array_merge(
    ['X-Forum-Php-Cache: MISS'],
    $threadFallbackHeaders,
    forum_asset_cache_headers(),
    forum_timing_headers($forumRequestStartedAt, 'cgi', $cgiStartedAt)
));
if (forum_mutating_request() && (int) $parsed['status_code'] >= 200 && (int) $parsed['status_code'] < 400) {
    forum_clear_cache();
    forum_clear_static_html();
}
