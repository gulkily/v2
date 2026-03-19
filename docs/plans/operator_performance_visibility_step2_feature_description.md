## Problem
Operators currently lack one recent, queryable view of which requests or non-request tasks are slow and which sub-step within each operation consumed the time. The next slice should make recent slow operations visible while they are running and after they complete or fail, without turning this loop into a broader monitoring platform.

## User Stories
- As an operator, I want to see recent slow operations across page loads, write flows, and non-request tasks so that I can identify where the system is spending time.
- As an operator, I want each operation to show named sub-step durations so that I can tell which component actually caused a multi-second delay.
- As an operator, I want in-progress and failed operations to remain visible so that incomplete work is still diagnosable.
- As a maintainer, I want one shared timing model across request and non-request work so that future instrumentation does not fragment into ad hoc logs.
- As a future developer, I want the first report to stay lightweight and recent-history-focused so that the slice remains small and usable.

## Core Requirements
- The slice must record one structured timing event per operation, including full HTTP request operations and selected non-request tasks.
- Each operation record must expose total duration and named sub-step durations, and remain visible from start through success or failure.
- The slice must retain only recent history, measured in hours, and prioritize recent diagnosis rather than long-term analytics.
- The first operator-facing report must show recent slow operations from the shared timing records rather than requiring direct log inspection.
- The slice must stay narrower than a full dashboard, metrics system, or alerting platform.

## Shared Component Inventory
- Existing HTTP request handling surfaces: reuse the current server request paths as the canonical source of request-timing operations because the feature is about visibility into current page-load and API behavior, not a new request model.
- Existing non-request maintenance and startup tasks: extend the current task entry points with the same timing model so request-triggered and non-request work share one operator-facing vocabulary.
- Existing operator-facing instance or status surface: reuse or extend the current in-app operator visibility page rather than introducing a separate admin product, because the immediate need is one lightweight recent-operations report.
- Existing application logging: keep it available for low-level debugging, but do not treat plain logs as the primary operator-facing source of truth for this slice.

## Simple User Flow
1. An HTTP request or non-request task begins.
2. The system records a live operation entry and updates it as named sub-steps complete.
3. The operation succeeds or fails, and the record remains available in recent history for a short retention window.
4. The operator opens the existing instance or status surface and reviews recent slow operations.
5. The operator inspects one slow operation and identifies which sub-step consumed the time.

## Success Criteria
- Operators can view recent slow operations for both HTTP requests and non-request tasks in one in-app report.
- Each recent operation includes enough sub-step timing detail to identify the slow component without reading raw logs first.
- In-progress and failed operations remain visible in the recent report during the retention window.
- The report is recent-history-focused and lightweight, without introducing a broader monitoring or analytics system.
