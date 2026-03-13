# Canonical Post Record V1

This document defines the minimal post record shape for the first implementation slice.

## Scope

- One ASCII text file represents one post.
- Canonical post files live in `records/posts/`.
- Sample files use the filename stem as the local `Post-ID`.
- This slice defines only enough structure to show thread roots, replies, and board tags.

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

## Body Rules

- The body is plain ASCII text.
- The body may include quoting and plain links.
- The body should remain understandable without rendering.

## Thread Semantics

- A thread root is a post with no `Thread-ID` and no `Parent-ID`.
- A reply references the thread root through `Thread-ID`.
- A reply references its immediate parent through `Parent-ID`.

## Example Thread Root

```text
Post-ID: root-001
Board-Tags: general meta
Subject: First thread

Hello world.
```

## Example Reply

```text
Post-ID: reply-001
Board-Tags: general meta
Thread-ID: root-001
Parent-ID: root-001

This is a reply.
```
