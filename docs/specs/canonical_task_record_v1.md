# Canonical Task Record V1

This document defines the minimal task record shape for repository-backed planning.

## Scope

- One ASCII text file represents one planning task.
- Canonical task files live in `records/tasks/`.
- Sample files use stable task IDs such as `T01` as the logical task identifier.
- This slice defines only enough structure to render a planning index, show dependency links, and optionally connect a task to one discussion thread.

## File Structure

A task file has two parts:

1. A contiguous header block at the top of the file
2. A body separated from the headers by one blank line

Headers use this form:

```text
Key: Value
```

## Required Headers

- `Task-ID`: unique identifier for the task within the repository
- `Title`: short human-readable task title
- `Status`: current planning status such as `proposed`
- `Presentability-Impact`: decimal rating from `0` to `1`
- `Implementation-Difficulty`: decimal rating from `0` to `1`
- `Sources`: semicolon-separated planning source references

## Optional Headers

- `Depends-On`: space-separated task IDs referenced by this task
- `Discussion-Thread-ID`: thread root post ID for the linked discussion thread

## Body Rules

- The body is plain ASCII text.
- The body holds the concise task summary shown in planning views.
- The body should remain understandable without special rendering.

## Semantics

- `Task-ID` is the canonical handle used for dependency links and task-detail routes.
- `Depends-On` references other visible task IDs from the same repository state.
- `Discussion-Thread-ID`, when present, points to an existing thread root in `records/posts/`.
- The initial implementation stores the current task state directly in the task file; append-only task-history records can be added in a later slice if needed.

## Example

```text
Task-ID: T01
Title: Publish raw planning files and debug views in the web UI
Status: proposed
Presentability-Impact: 0.94
Implementation-Difficulty: 0.34
Sources: todo.txt; docs/plans/forum_feature_splitting_checklist.md

Extend the current planning page into a real transparency surface so the system is
easier to inspect and iterate on.
```
