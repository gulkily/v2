# Compose Reply Latency Reduction Step 2: Feature Description

## Problem
`/compose/reply` is slow in production because it misses the current PHP fast paths and the Python handler does more repository work than the page needs. The next slice should reduce reply-compose latency now by shrinking the Python path and define a clean end state where the route can be served fully from PHP without depending on Python components.

## User Stories
- As a user replying to a thread, I want `/compose/reply` to open quickly so that joining a conversation does not feel stalled.
- As an operator, I want reply compose to avoid the slow Python path in steady state so that production read latency is predictable and cheaper to serve.
- As a maintainer, I want the reply-compose route to depend on a small explicit data contract so that the current Python implementation can be simplified and later mirrored in PHP without hidden coupling.
- As a future performance investigator, I want reply-compose latency to be attributable to clear route boundaries so that regressions can be diagnosed without guessing whether the cost comes from PHP routing, Python startup, or oversized repository reads.

## Core Requirements
- The feature must materially reduce production latency for `/compose/reply` without changing the current reply submission contract or compose URL shape.
- The intermediate slice must simplify the Python route so it only loads the thread, parent-post, moderation, and author context actually needed for reply compose.
- The final route boundary must support a full PHP-native `/compose/reply` implementation that no longer requires Python components for ordinary read rendering.
- The feature must preserve current moderation visibility, locked-thread behavior, and reply-target validation semantics.
- The feature must keep `/compose/reply` aligned with the existing compose UI and browser-signing flow instead of introducing a second compose experience.

## Shared Component Inventory
- Existing compose page shell in `templates/compose.html`: reuse as the canonical reply-compose UI so Python and PHP render the same browser-signing surface rather than diverging.
- Existing browser signing assets such as `/assets/browser_signing.js` and `/assets/openpgp_loader.js`: reuse unchanged as the canonical client-side compose behavior because this feature is about server-side render latency, not a new signing flow.
- Existing Python `/compose/reply` route in `forum_web/web.py`: extend and simplify it as the interim canonical implementation because it already defines the current moderation and reply-target behavior.
- Existing reply-reference rendering surface used by compose reply: reuse the canonical reply-context presentation so the PHP route mirrors the same user-visible target post rather than inventing a new summary card.
- Existing PHP host routing and caching surfaces in `php_host/public/index.php` and `php_host/public/cache.php`: extend these as the canonical non-Python read path rather than introducing a separate adapter for compose reply.
- Existing PHP-native read artifact strategy in `forum_core/php_native_reads.py` and related snapshot storage: extend this contract for the final PHP-native route so compose reply follows the same primary-host architecture as other PHP-served reads.

## Simple User Flow
1. User opens `/compose/reply?thread_id=...&parent_id=...`.
2. The server resolves the requested thread and visible parent reply context using the minimal data needed for compose rendering.
3. The page renders the existing compose UI with the same reply-target reference, moderation behavior, and browser-signing tools as today.
4. In the final state, ordinary reply-compose reads are served through the PHP host without requiring Python execution.
5. User writes and submits the reply through the existing compose and API flow.

## Success Criteria
- Production `/compose/reply` latency is materially lower than the current baseline for ordinary reply-compose reads.
- The route no longer performs broad repository loading when only one thread and one parent-post context are needed.
- The final route contract is explicit enough that `/compose/reply` can be served from PHP without relying on Python rendering components.
- User-visible reply-compose behavior remains unchanged for visible posts, hidden posts, and locked threads.
- Production verification can distinguish whether `/compose/reply` is still using a Python-backed fallback or has reached the intended PHP-native path.
