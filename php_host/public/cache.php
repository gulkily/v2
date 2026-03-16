<?php

declare(strict_types=1);

const FORUM_PHP_MICROCACHE_TTL_SECONDS = 5;
const FORUM_PHP_ASSET_CACHE_MAX_AGE_SECONDS = 3600;

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
    if ($candidate === '/assets/task_priorities.js') {
        return $candidate;
    }
    if ($candidate === '/assets/vendor/openpgp.min.mjs') {
        return $candidate;
    }
    return null;
}

function forum_cacheable_read_request(): bool
{
    if (forum_request_method() !== 'GET') {
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
    $configured = getenv('FORUM_PHP_CACHE_DIR');
    if (is_string($configured) && $configured !== '') {
        return rtrim($configured, DIRECTORY_SEPARATOR);
    }
    return rtrim(sys_get_temp_dir(), DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . 'forum_php_cache';
}

function forum_microcache_ttl_seconds(): int
{
    $configured = getenv('FORUM_PHP_MICROCACHE_TTL');
    if (!is_string($configured) || $configured === '') {
        return FORUM_PHP_MICROCACHE_TTL_SECONDS;
    }
    $ttl = (int) $configured;
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
