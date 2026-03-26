## Problem
The PHP-hosted production path still depends on per-request Python CGI execution for cold misses and dynamic public reads, which keeps latency and runtime overhead higher than necessary. The next slice should let the PHP host answer a narrow set of hot anonymous read routes from a shared read contract without turning the system into two unrelated applications.

## User Stories
- As an operator on a PHP-hosted deployment, I want core public read pages to avoid per-request Python execution more often so that traffic spikes are cheaper and page loads are faster.
- As an anonymous reader, I want board, thread, post, or profile pages to load quickly on the PHP-hosted site even when a cache or static artifact is cold.
- As a maintainer, I want the duplicated PHP path to follow one explicit shared spec so that Python and PHP implementations stay aligned instead of drifting silently.
- As a maintainer, I want Python to remain authoritative for writes and shared data preparation so that the duplicate path stays narrow and auditable.

## Core Requirements
- The first duplicated PHP path must cover only an explicit allowlist of hot anonymous public read routes rather than the full application.
- The feature must define one shared cross-runtime read contract covering route eligibility, normalized inputs, derived data shape, visibility rules, and cache invalidation boundaries.
- Python must remain the source of truth for writes, read-model preparation, and any derived artifacts or indexed data that the PHP path consumes.
- Non-allowlisted routes, personalized views, write flows, and request-sensitive behavior must continue to use the current PHP-to-Python path.
- The slice must improve PHP-host performance without creating a second independent product surface or a broad rewrite of page behavior in PHP.

## Shared Component Inventory
- Existing PHP host entry layer in [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php) and [`php_host/public/cache.php`](/home/wsl/v2/php_host/public/cache.php): extend as the canonical PHP-host execution boundary because this is where requests already decide between cached, static, and CGI-backed behavior.
- Existing canonical Python read renderer in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py): keep as the authoritative definition of route semantics and current output while the shared read contract is being defined.
- Existing derived read surfaces such as the post index and related cached artifacts in [`forum_core/post_index.py`](/home/wsl/v2/forum_core/post_index.py): reuse or extend as the shared prepared-data boundary rather than making PHP parse the raw repository independently on every request.
- Existing static HTML and PHP-host refresh workflows in [`scripts/forum_tasks.py`](/home/wsl/v2/scripts/forum_tasks.py) and PHP host config/setup helpers: reuse as the current invalidation and deployment boundary so the new read path fits the production host model.
- Existing public route surfaces for boards, threads, posts, and profiles: evaluate as candidates for the allowlist, but do not assume all of them belong in the first duplicated slice.

## Simple User Flow
1. An anonymous visitor requests a hot public read route on the PHP-hosted site.
2. The PHP host determines whether that route belongs to the allowlisted duplicated read path.
3. If it does, PHP answers the request from the shared prepared read contract without invoking Python CGI for that response.
4. If it does not, the request continues through the existing PHP-to-Python path.
5. When forum content changes, the shared prepared data and cache invalidation flow keep later PHP and Python reads aligned.

## Success Criteria
- At least one explicit class of hot anonymous public read routes can be served on the PHP-hosted path without per-request Python CGI execution.
- The duplicated path is governed by one documented shared read contract rather than informal behavior copied from Python templates or handlers.
- Writes, request-sensitive routes, and non-allowlisted reads continue to use the current Python-backed path without regression.
- PHP-host latency improves on the covered routes in a way that is meaningful to operators, not just a code-organization exercise.
- The slice establishes a sustainable pattern for intentional duplicate runtime paths instead of an ad hoc fork.
