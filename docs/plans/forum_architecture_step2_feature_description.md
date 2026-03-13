## Problem
Build a forum/message board system whose canonical data is human-readable ASCII text tracked in git, authenticated with minimal OpenPGP-based PKI, and usable equally through a web interface, simple text APIs, and agent-friendly tooling.

## User Stories
- As a human user, I want to read and post through a browser so that I can use the forum locally or on a public server without custom client software.
- As an agent or technical user, I want a simple API and text-native data model so that I can read, generate, sign, and submit content programmatically.
- As a self-hosting user, I want to sync or fork the forum state with git so that I can keep a local copy, inspect history, and run an independent instance.
- As a moderator or operator, I want signed identities and auditable content history so that trust decisions and moderation actions are inspectable.
- As an alternative backend implementer, I want a narrow execution contract so that I can reimplement the server behavior in different languages without changing the data format or client behavior.

## Core Requirements
- Canonical application data must be stored as ASCII-only text files in a git-tracked repository, with one canonical payload file per post.
- The discussion model must use a flat global thread space with board tags, linear thread presentation, quoted cross-links, and chronological ordering in version 1.
- Authentication and authorship must be PKI-based, with minimal OpenPGP-compatible signing usable both in-browser and through command-line tooling.
- The primary interface must be web-based and runnable both on localhost and on a public internet-facing server.
- The system must expose a straightforward plain-text read/write API that supports posting, retrieval, and sync-friendly automation for users and agents, alongside git as the canonical sync mechanism.
- The system must support immediate soft-deletes for live public operation while also tolerating later hard deletion of sensitive content from the repository and rewritten history.
- Backend behavior must be defined by a small, language-agnostic CGI-style contract so multiple interchangeable implementations can operate on the same repository state and produce the same visible forum state.

## Shared Component Inventory
- Existing UI surfaces: none; the web UI will be a new canonical interface over the text/git data model.
- Existing API surfaces: none; the HTTP API will be a new canonical interface and should be stable enough for agents and CLI tooling.
- Existing backend surfaces: none; the backend contract should be defined once and reused across reference implementations rather than duplicated ad hoc.
- Existing auth surfaces: none; OpenPGP signing and verification flows will become the canonical identity mechanism across browser, CLI, and server flows.

## Simple User Flow
1. A user or agent obtains or imports an OpenPGP keypair.
2. The user browses tagged threads through a local or public web instance, or reads the same data through the API or git.
3. The user or agent creates a new thread or reply, signs the canonical payload when required by instance policy, and submits it through the text API or web client.
4. The server applies local policy, verifies signatures when present, records the post in the canonical ASCII text format, and tracks the change in git-backed storage.
5. Other users, agents, or mirrored instances retrieve the updated content through the web UI, API, or git-based sync workflows.

## Success Criteria
- Core content and metadata are represented in ASCII-only text files that remain understandable without specialized tooling.
- A browser user can generate or import an OpenPGP key, authenticate, and post through the web UI.
- A CLI user or agent can read and submit the same content using documented text formats, APIs, and git workflows.
- A locally hosted instance and a public server can operate on the same repository structure and produce equivalent visible forum state.
- At least one alternate backend implementation can be introduced without changing the canonical data model or client-facing protocol.
