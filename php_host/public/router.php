<?php

declare(strict_types=1);

$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
$requested = $path === false ? '/' : $path;
$publicDir = __DIR__;
$target = realpath($publicDir . $requested);
$publicPrefix = $publicDir . DIRECTORY_SEPARATOR;

if (is_string($target) && strpos($target, $publicPrefix) === 0 && is_file($target)) {
    return false;
}

require $publicDir . DIRECTORY_SEPARATOR . 'index.php';
