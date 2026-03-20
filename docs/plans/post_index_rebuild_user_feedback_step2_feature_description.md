## Problem
Some ordinary page loads can still trigger a full post-index rebuild when the derived index is stale, which currently appears to the user as an unexplained long wait. The next slice should make that wait understandable in the product without turning the work into a broader background-jobs or indexing redesign project.

## User Stories
- As a reader, I want clear feedback when a page load is waiting on reindexing so that the delay feels explained rather than broken.
- As a reader, I want the feedback to tell me that forum data is being prepared so that I understand the page is still working.
- As an operator, I want reindex-triggered waits to map cleanly to the existing recent-operations visibility so that user-facing delays are diagnosable from the current status surface.
- As a maintainer, I want this slice to reuse the current indexed-read flow so that we improve clarity without introducing a second indexing lifecycle.

## Core Requirements
- The product must show explicit user-facing feedback when a request-triggered post-index rebuild is in progress instead of presenting only a long blank or stalled page load.
- The feedback must be tied to the existing request and derived-index lifecycle, not a separate background-task system.
- The first slice must cover the canonical indexed read experiences where users are most likely to encounter rebuild-triggered waits.
- The user-facing messaging must make clear that the system is preparing or refreshing forum data, without exposing raw internal diagnostics.
- The feature must preserve the current recent slow-operations visibility as the operator-facing source of truth for the same work.

## Shared Component Inventory
- Indexed read path in `forum_core/post_index.py`: extend the canonical `ensure_post_index_current(...)` and related indexed-read lifecycle rather than inventing a parallel reindex trigger, because this is the source of rebuild-triggered waits today.
- Board and thread reading surfaces in `forum_web/web.py`: reuse or extend the existing forum page rendering entry points that depend on indexed reads, because these are the canonical user-facing pages where the slow wait is experienced.
- Existing site page shell and templates in `forum_web/web.py` and `templates/`: extend the current page-level rendering surfaces for the loading or waiting presentation rather than creating a separate mini-app, because the feature is about better feedback inside the existing web experience.
- Recent slow operations surface in `forum_core/operation_events.py` and `forum_web/web.py`: reuse the current operation-events model and recent-operations page as the canonical operator-facing status source, because the same rebuild should remain diagnosable there without duplicating reporting.
- Passive logs in server output: keep available for low-level debugging, but do not treat logs as the primary product surface for this slice.

## Simple User Flow
1. A reader opens a board, thread, profile, or other page that depends on indexed forum data.
2. The system detects that the post index is stale and starts the existing rebuild path.
3. The user sees explicit in-app feedback that forum data is being refreshed for the requested page.
4. The rebuild completes and the requested page content becomes available.
5. If the rebuild was slow, the same work remains visible in the existing recent slow-operations surface for operator diagnosis.

## Success Criteria
- Users no longer experience reindex-triggered waits as an unexplained long page load on the covered indexed-read pages.
- The user-facing feedback clearly communicates that the system is refreshing or preparing forum data for the request.
- The slice reuses the current indexed-read and operation-visibility model instead of introducing a separate background processing workflow.
- Operators can still correlate slow user-facing waits with the existing recent slow-operations surface.
