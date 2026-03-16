<?php

declare(strict_types=1);

require_once __DIR__ . '/cache.php';

function forum_app_root(): string
{
    $configured = getenv('FORUM_PHP_APP_ROOT');
    if (is_string($configured) && $configured !== '') {
        return rtrim($configured, DIRECTORY_SEPARATOR);
    }

    return dirname(__DIR__, 2);
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
forum_store_cached_response($parsed, $response);
forum_apply_cgi_response($response, array_merge(['X-Forum-Php-Cache: MISS'], forum_asset_cache_headers()));
