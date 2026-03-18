## Problem
Admins and developers currently have to remember several direct script and test commands to do routine work in this repo. The next slice should add one short git-style repo command that makes common tasks discoverable while keeping the task contract stable enough for side-by-side Python and Perl implementations later.

## User Stories
- As a developer, I want one short repo command for common tasks so that I do not have to remember script paths and long command lines.
- As an admin/operator, I want the same command to expose routine local tasks through one help surface so that repo operations are easier to discover and repeat.
- As a future backend implementer, I want the command contract to stay language-neutral so Python and Perl runners can satisfy the same user-facing behavior.
- As a reviewer, I want the existing direct scripts to remain usable so parity checks and low-level debugging do not depend on one wrapper implementation.

## Core Requirements
- The slice must add one short repo-root command with git-style subcommands for common admin/developer tasks.
- The canonical contract must be implementation-neutral: subcommand names, arguments, exit behavior, and high-level help/output must remain stable even if the backing runner changes from Python to Perl or supports both side by side.
- The initial task set must cover the repetitive repo workflows that already exist today, including local server startup and test execution, rather than inventing unrelated new task categories.
- The slice must treat the wrapper as a convenience and discovery surface only; direct underlying scripts and CGI-style commands must remain valid for testing, fixtures, and future parity work.
- The slice must avoid adding new browser UI, HTTP API behavior, or parallel configuration names just for the task command.

## Shared Component Inventory
- Existing local server surface: reuse `scripts/run_read_only.py` as the canonical local forum startup path; the new command should wrap or delegate to this behavior rather than replacing it.
- Existing test surface: reuse the current unittest-based `tests/` workflow as the canonical test behavior; the new command standardizes invocation, not test semantics.
- Existing write-command surface: preserve `cgi-bin/create_thread.py` and `cgi-bin/create_reply.py` as direct language-neutral write entrypoints; the task command must not redefine their request/response contract.
- Existing runtime-config surface: reuse the current `FORUM_*` environment-based configuration and planned `.env` workflow rather than introducing command-only config names.
- New command surface: add one repo-root wrapper with a stable subcommand contract because the project currently has no short canonical command for routine repo tasks.

## Simple User Flow
1. An admin or developer runs the repo command with no arguments or `help` to see the supported tasks.
2. They choose a common task such as starting the local server or running tests.
3. The repo command dispatches that request to the active backend runner while preserving the canonical subcommand and argument shape.
4. The selected backend executes the existing underlying task behavior and returns a stable exit result.
5. Later, a Perl runner can be added behind the same command contract without forcing users to relearn the command surface.

## Success Criteria
- One obvious repo-root command exists and makes common tasks discoverable through help output.
- A user can start the local forum and run the test suite through that command without recalling the current direct script paths.
- Existing direct scripts and CGI-style commands continue to work unchanged for debugging and parity checks.
- The documented command contract is stable enough that a Python runner and a later Perl runner can coexist behind the same user-facing subcommands.
- The feature improves operator/developer ergonomics without changing canonical forum data formats, HTTP contracts, or runtime setting names.
