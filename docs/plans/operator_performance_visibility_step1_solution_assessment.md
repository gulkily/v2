# Operator Performance Visibility Step 1: Solution Assessment

## Problem Statement
Choose the smallest useful way to capture recent slow operations across HTTP requests and non-request work with enough sub-step timing detail to identify what is actually slow.

### Option A: Record structured operation-timing events in a recent local store and expose a simple recent-operations report
- Pros:
  - Captures the unit that matters for diagnosis: one operation with total duration, sub-step durations, start time, completion state, and failure state.
  - Covers both request-triggered flows and non-request work such as startup checks, rebuilds, or maintenance tasks under one model.
  - Supports live visibility because operations can be recorded when they start, updated while running, and finalized on success or failure.
  - Gives a straightforward path to a web report showing recent slow operations without requiring a broader monitoring system.
  - Fits the current deployment assumptions because one server process with concurrent requests can write to one recent local store with short retention.
- Cons:
  - Larger than logs alone because it needs a small durable event store and one operator-facing read surface.
  - Requires explicit choices about retention, event schema, and how much identifying context is safe to retain.

### Option B: Emit sampled structured timing logs only and inspect them outside the app
- Pros:
  - Smallest implementation surface.
  - Still allows phase-level timing detail if each operation emits structured sub-step durations.
  - Avoids adding an in-app store or report surface in the first slice.
- Cons:
  - Weak fit for the stated goal of seeing recent slow operations in the app, especially for in-progress or failed non-request work.
  - Makes recent-history review and comparison less convenient because operators must inspect logs directly.
  - Leaves the eventual web report dependent on building a second ingestion or parsing layer later.

### Option C: Build a richer operator dashboard or broader monitoring system first
- Pros:
  - Could provide richer filtering, aggregation, current-state tracking, and longer-term history.
  - Leaves room for future queue management, alerts, and deeper operational reporting.
- Cons:
  - Much larger scope than the current need.
  - Risks turning a focused timing-diagnosis loop into a full observability project.
  - Delays the immediate goal of seeing which sub-step is slow for recent requests and maintenance tasks.

## Recommendation
Recommend Option A: record structured operation-timing events in a recent local store and expose a simple recent-operations report.

This is the smallest coherent slice because the real need is not just “more logs” or a generic status page. The need is to inspect recent slow operations, including in-progress and failed ones, and see which named sub-step consumed the time. A shared operation-event model solves that directly for both HTTP requests and non-request work, while keeping the reporting surface small.

Assumptions for Step 2:
- The primary source of truth is one structured timing event per operation rather than plain log lines.
- The useful unit is operation-level timing with named sub-step durations, not only coarse request totals.
- The slice covers full HTTP request timing and non-request processes that may run outside request handling.
- Operations are recorded when they start, remain visible while running, and are finalized on success or failure.
- Retention is short, measured in hours, and optimized for recent diagnosis rather than long-term analytics.
- A small local recent-event store, such as a separate SQLite database, is an acceptable backing store for this slice.
- The first report should focus on recent slow operations rather than richer dashboards or aggregate charts.
