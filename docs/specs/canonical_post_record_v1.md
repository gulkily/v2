# Canonical Post Record V1

This document defines the canonical post record shape for the current implementation slice.

## Scope

- One ASCII text file represents one post.
- Canonical post files live in `records/posts/`.
- Sample files use the filename stem as the local `Post-ID`.
- This slice defines thread roots, replies, board tags, and typed root-thread metadata.

## File Structure

A post file has two parts:

1. A contiguous header block at the top of the file
2. A body separated from the headers by one blank line

Headers use this form:

```text
Key: Value
```

## Required Headers

- `Post-ID`: unique identifier for the post within the repository
- `Board-Tags`: space-separated board tags

## Conditional Headers

- `Thread-ID`: required for replies, omitted for thread roots
- `Parent-ID`: required for replies, omitted for thread roots
- `Subject`: optional, mainly useful for thread roots
- `Thread-Type`: optional for thread roots, omitted for replies

## Typed Root Headers

Typed root metadata is reserved for thread roots. Replies must not include `Thread-Type`
or subtype-specific headers.

The first supported typed root is `Thread-Type: task`. Task roots add:

- `Task-Status`: short task state label such as `proposed`
- `Task-Presentability-Impact`: decimal rating from `0` to `1`
- `Task-Implementation-Difficulty`: decimal rating from `0` to `1`
- `Task-Depends-On`: optional space-separated root post IDs for task dependencies
- `Task-Sources`: optional semicolon-separated provenance references

## Body Rules

- The body is plain ASCII text.
- The body may include quoting and plain links.
- The body should remain understandable without rendering.

## Thread Semantics

- A thread root is a post with no `Thread-ID` and no `Parent-ID`.
- A reply references the thread root through `Thread-ID`.
- A reply references its immediate parent through `Parent-ID`.
- A typed root thread is still a normal thread root. Replies remain ordinary replies.
- For this slice, authoritative task state lives on the task root post. Future slices may
  add append-only task-update records instead of overloading replies.

## Example Thread Root

```text
Post-ID: root-001
Board-Tags: general meta
Subject: First thread

Hello world.
```

## Example Task Thread Root

```text
Post-ID: T01
Board-Tags: planning
Subject: Publish raw planning files and debug views in the web UI
Thread-Type: task
Task-Status: proposed
Task-Presentability-Impact: 0.94
Task-Implementation-Difficulty: 0.34
Task-Sources: todo.txt; docs/plans/forum_feature_splitting_checklist.md

Expose todo.txt, ideas.txt, and raw object/debug views from the interface.
```

## Example Reply

```text
Post-ID: reply-001
Board-Tags: general meta
Thread-ID: root-001
Parent-ID: root-001

This is a reply.
```
