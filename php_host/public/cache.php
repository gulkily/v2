<?php

declare(strict_types=1);

const FORUM_PHP_MICROCACHE_TTL_SECONDS = 5;
const FORUM_PHP_ASSET_CACHE_MAX_AGE_SECONDS = 3600;
const FORUM_PHP_POST_INDEX_REBUILD_QUERY_PARAM = '__forum_rebuild';

function forum_request_path(): string
{
    return parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
}

function forum_request_method(): string
{
    $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
    return is_string($method) ? strtoupper($method) : 'GET';
}

function forum_request_query_string(): string
{
    $query = $_SERVER['QUERY_STRING'] ?? '';
    return is_string($query) ? $query : '';
}

function forum_request_query_param(string $name): ?string
{
    $query = forum_request_query_string();
    if ($query === '') {
        return null;
    }
    parse_str($query, $params);
    $value = $params[$name] ?? null;
    if (is_string($value)) {
        return $value;
    }
    return null;
}

function forum_post_index_rebuild_request(): bool
{
    $value = forum_request_query_param(FORUM_PHP_POST_INDEX_REBUILD_QUERY_PARAM);
    if ($value === null) {
        return false;
    }
    return in_array(strtolower(trim($value)), ['1', 'true', 'yes', 'on'], true);
}

function forum_asset_request_path(?string $path = null): ?string
{
    $candidate = $path ?? forum_request_path();
    if (!str_starts_with($candidate, '/assets/')) {
        return null;
    }
    if ($candidate === '/assets/site.css') {
        return $candidate;
    }
    if ($candidate === '/assets/browser_signing.js') {
        return $candidate;
    }
    if ($candidate === '/assets/copy_field.js') {
        return $candidate;
    }
    if ($candidate === '/assets/task_priorities.js') {
        return $candidate;
    }
    if ($candidate === '/assets/vendor/openpgp.min.mjs') {
        return $candidate;
    }
    return null;
}

function forum_static_html_request_path(?string $path = null): ?string
{
    $candidate = $path ?? forum_request_path();
    if ($candidate === '/' || $candidate === '/instance/' || $candidate === '/moderation/') {
        return $candidate;
    }
    if ($candidate === '/planning/task-priorities' || $candidate === '/planning/task-priorities/') {
        return $candidate;
    }
    if (str_starts_with($candidate, '/threads/')) {
        return str_ends_with($candidate, '/') ? $candidate : $candidate . '/';
    }
    if (str_starts_with($candidate, '/posts/')) {
        return str_ends_with($candidate, '/') ? $candidate : $candidate . '/';
    }
    if (str_starts_with($candidate, '/planning/tasks/')) {
        return str_ends_with($candidate, '/') ? $candidate : $candidate . '/';
    }
    if (str_starts_with($candidate, '/profiles/')) {
        if (str_contains($candidate, '/update') || str_contains($candidate, '/merge')) {
            return null;
        }
        return str_ends_with($candidate, '/') ? $candidate : $candidate . '/';
    }
    return null;
}

function forum_static_html_request(): bool
{
    if (forum_request_method() !== 'GET') {
        return false;
    }
    if (forum_post_index_rebuild_request()) {
        return false;
    }
    if (isset($_SERVER['HTTP_AUTHORIZATION']) || isset($_SERVER['PHP_AUTH_USER']) || isset($_SERVER['HTTP_COOKIE'])) {
        return false;
    }
    if (forum_request_query_string() !== '') {
        return false;
    }

    $path = forum_request_path();
    if (forum_asset_request_path($path) !== null) {
        return false;
    }
    if (str_starts_with($path, '/api/')) {
        return false;
    }
    if ($path === '/favicon.ico' || $path === '/llms.txt') {
        return false;
    }
    return forum_static_html_request_path($path) !== null;
}

function forum_static_html_dir(): string
{
    $configured = forum_host_config()['static_html_dir'] ?? '';
    if (is_string($configured) && $configured !== '') {
        return rtrim($configured, DIRECTORY_SEPARATOR);
    }
    return forum_public_dir() . DIRECTORY_SEPARATOR . '_static_html';
}

function forum_static_html_public_path(string $requestPath, string $queryString = ''): ?string
{
    if ($queryString !== '') {
        return null;
    }
    $normalizedPath = forum_static_html_request_path($requestPath);
    if ($normalizedPath === null || str_contains($normalizedPath, '..')) {
        return null;
    }
    $staticRoot = forum_static_html_dir();
    if ($normalizedPath === '/') {
        return $staticRoot . DIRECTORY_SEPARATOR . 'index.html';
    }

    $trimmed = trim($normalizedPath, '/');
    if ($trimmed === '') {
        return $staticRoot . DIRECTORY_SEPARATOR . 'index.html';
    }
    return $staticRoot . DIRECTORY_SEPARATOR . $trimmed . DIRECTORY_SEPARATOR . 'index.html';
}

function forum_read_static_html(): ?string
{
    if (!forum_static_html_request()) {
        return null;
    }
    $path = forum_static_html_public_path(forum_request_path(), forum_request_query_string());
    if ($path === null || !is_file($path)) {
        return null;
    }
    $body = @file_get_contents($path);
    return is_string($body) ? $body : null;
}

function forum_store_static_html(array $parsedResponse): void
{
    if (!forum_static_html_request()) {
        return;
    }
    if ((int) $parsedResponse['status_code'] !== 200) {
        return;
    }
    $contentType = '';
    foreach ($parsedResponse['headers'] as $header) {
        if (stripos($header, 'Content-Type:') === 0) {
            $contentType = trim(substr($header, strlen('Content-Type:')));
            break;
        }
    }
    if ($contentType === '' || stripos($contentType, 'text/html') !== 0) {
        return;
    }
    $path = forum_static_html_public_path(forum_request_path(), forum_request_query_string());
    if ($path === null) {
        return;
    }
    $directory = dirname($path);
    if (!is_dir($directory) && !@mkdir($directory, 0775, true) && !is_dir($directory)) {
        return;
    }
    @file_put_contents($path, (string) $parsedResponse['body'], LOCK_EX);
}

function forum_clear_static_html(): void
{
    $staticRoot = forum_static_html_dir();
    if (!is_dir($staticRoot)) {
        return;
    }

    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($staticRoot, FilesystemIterator::SKIP_DOTS),
        RecursiveIteratorIterator::CHILD_FIRST
    );
    foreach ($iterator as $entry) {
        if ($entry->isDir()) {
            @rmdir($entry->getPathname());
            continue;
        }
        @unlink($entry->getPathname());
    }
}

function forum_cacheable_read_request(): bool
{
    if (forum_request_method() !== 'GET') {
        return false;
    }
    if (forum_post_index_rebuild_request()) {
        return false;
    }
    if (isset($_SERVER['HTTP_AUTHORIZATION']) || isset($_SERVER['PHP_AUTH_USER']) || isset($_SERVER['HTTP_COOKIE'])) {
        return false;
    }

    $path = forum_request_path();
    if (forum_asset_request_path($path) !== null) {
        return false;
    }
    if ($path === '/' || $path === '/instance/' || $path === '/llms.txt' || $path === '/moderation/') {
        return true;
    }
    if (
        $path === '/api/'
        || $path === '/api/list_index'
        || $path === '/api/get_thread'
        || $path === '/api/get_post'
        || $path === '/api/get_profile'
        || $path === '/api/get_moderation_log'
    ) {
        return true;
    }
    if ($path === '/planning/task-priorities' || $path === '/planning/task-priorities/') {
        return true;
    }
    if (str_starts_with($path, '/threads/')) {
        return true;
    }
    if (str_starts_with($path, '/posts/')) {
        return true;
    }
    if (str_starts_with($path, '/planning/tasks/')) {
        return true;
    }
    if (str_starts_with($path, '/profiles/')) {
        return true;
    }
    return false;
}

function forum_cache_dir(): string
{
    $configured = forum_host_config()['cache_dir'] ?? '';
    if (is_string($configured) && $configured !== '') {
        return rtrim($configured, DIRECTORY_SEPARATOR);
    }
    $fallback = getenv('FORUM_PHP_CACHE_DIR');
    if (is_string($fallback) && $fallback !== '') {
        return rtrim($fallback, DIRECTORY_SEPARATOR);
    }
    return rtrim(sys_get_temp_dir(), DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . 'forum_php_cache';
}

function forum_microcache_ttl_seconds(): int
{
    $configured = forum_host_config()['microcache_ttl'] ?? null;
    if (is_int($configured) && $configured > 0) {
        return $configured;
    }
    if (is_string($configured) && $configured !== '') {
        $ttl = (int) $configured;
        if ($ttl > 0) {
            return $ttl;
        }
    }
    $fallback = getenv('FORUM_PHP_MICROCACHE_TTL');
    if (!is_string($fallback) || $fallback === '') {
        return FORUM_PHP_MICROCACHE_TTL_SECONDS;
    }
    $ttl = (int) $fallback;
    return $ttl > 0 ? $ttl : FORUM_PHP_MICROCACHE_TTL_SECONDS;
}

function forum_cache_key(): string
{
    return hash('sha256', forum_request_method() . "\n" . forum_request_path() . "\n" . forum_request_query_string());
}

function forum_cache_file_path(): string
{
    return forum_cache_dir() . DIRECTORY_SEPARATOR . forum_cache_key() . '.cgi';
}

function forum_cache_fresh(string $cacheFile): bool
{
    if (!is_file($cacheFile)) {
        return false;
    }
    $modifiedAt = filemtime($cacheFile);
    if ($modifiedAt === false) {
        return false;
    }
    return (time() - $modifiedAt) <= forum_microcache_ttl_seconds();
}

function forum_read_cached_response(): ?string
{
    if (!forum_cacheable_read_request()) {
        return null;
    }
    $cacheFile = forum_cache_file_path();
    if (!forum_cache_fresh($cacheFile)) {
        return null;
    }
    $cached = @file_get_contents($cacheFile);
    return is_string($cached) ? $cached : null;
}

function forum_store_cached_response(array $parsedResponse, string $response): void
{
    if (!forum_cacheable_read_request()) {
        return;
    }
    if ((int) $parsedResponse['status_code'] !== 200) {
        return;
    }
    $cacheDir = forum_cache_dir();
    if (!is_dir($cacheDir) && !@mkdir($cacheDir, 0775, true) && !is_dir($cacheDir)) {
        return;
    }
    @file_put_contents(forum_cache_file_path(), $response, LOCK_EX);
}

function forum_asset_cache_headers(): array
{
    if (forum_asset_request_path() === null) {
        return [];
    }
    return ['Cache-Control: public, max-age=' . FORUM_PHP_ASSET_CACHE_MAX_AGE_SECONDS];
}

function forum_mutating_request(): bool
{
    return forum_request_method() !== 'GET' && forum_request_method() !== 'HEAD';
}

function forum_clear_cache(): void
{
    $cacheDir = forum_cache_dir();
    if (!is_dir($cacheDir)) {
        return;
    }
    $entries = scandir($cacheDir);
    if ($entries === false) {
        return;
    }
    foreach ($entries as $entry) {
        if ($entry === '.' || $entry === '..') {
            continue;
        }
        $path = $cacheDir . DIRECTORY_SEPARATOR . $entry;
        if (is_file($path)) {
            @unlink($path);
        }
    }
}
