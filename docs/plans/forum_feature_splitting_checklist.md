# Forum Feature Splitting Checklist

Purpose: break the current architecture into smaller future FDP loops so each loop can produce a visible, testable result without requiring the whole system to be solved first.

This is not a Step 3 development plan. It is a checklist of candidate feature slices.

## Recommended Early Demonstration Path

- [x] Loop 1: Repository layout and canonical post format
  - Goal: define the on-disk shape for posts and a tiny sample dataset.
  - Includes: repository directories, one-file-per-post rule, header/body format, ASCII-only constraints, sample records.
  - Demonstrable result: a repo with hand-authored sample posts that can be inspected directly in a text editor and in git history.

- [x] Loop 2: Read-only thread and index rendering
  - Goal: render the sample repository through a local web interface.
  - Includes: board-tag index, thread view, permalink view, deterministic parsing, no write path yet.
  - Demonstrable result: a local web app that reads text files from the repo and displays browsable threads.

- [x] Loop 3: Read-only plain-text HTTP API
  - Goal: expose the same read views through the CGI-style API contract.
  - Includes: `list_index`, `get_thread`, `get_post`.
  - Demonstrable result: browser UI and API both show the same content from the same repository state.

- [x] Loop 4: Basic posting without identity richness
  - Goal: allow creation of new threads and replies with minimal required fields.
  - Includes: `create_thread`, `create_reply`, canonical payload validation, direct git commits.
  - Demonstrable result: a user can create a thread locally and immediately see it in the UI and API.

- [x] Loop 5: Browser key generation and detached signing
  - Goal: add minimal OpenPGP-backed posting from the browser.
  - Includes: key generation/import, detached signatures, server-side verification when required.
  - Demonstrable result: signed posting works end-to-end from a browser and from CLI tooling.

## Follow-On Slices

- [x] Loop 6: Identity bootstrap and profile read model
  - Goal: make key-post bootstrap and profile lookup coherent.
  - Includes: public-key bootstrap post shape, profile summary derivation, user/profile view.
  - Demonstrable result: a user identity can be created and viewed from repository data.

- [x] Loop 7: Moderation record model
  - Goal: introduce signed moderation actions as first-class records.
  - Includes: moderation log, hide, lock, pin, unpin record types, visible-state rules.
  - Demonstrable result: a moderator action changes what the public instance shows and appears in the moderation log.

- [ ] Loop 8: Soft-delete behavior
  - Goal: support immediate public-instance removal without hard purge.
  - Includes: tombstone or moderation delete records, read-path behavior, UI treatment for deleted content.
  - Demonstrable result: content disappears from the live instance while remaining auditable in current repo state.

- [ ] Loop 9: Hard purge tolerance
  - Goal: make the system tolerate removal of sensitive content from repo state and rewritten history.
  - Includes: purged-record handling, `get_post` and `get_thread` error/placeholder behavior, index rebuilding after purge.
  - Demonstrable result: after a purge, the system still serves the remaining forum state cleanly.

- [ ] Loop 10: Multi-implementation parity harness
  - Goal: verify that Perl and Python implementations produce the same success output.
  - Includes: shared fixtures, deterministic output tests, byte-identical response comparison.
  - Demonstrable result: the same repository and request fixture pass in both implementations.

- [ ] Loop 11: Git and HTTP sync model
  - Goal: clarify how local clones, mirrors, and HTTP clients move content around.
  - Includes: canonical git sync workflows, HTTP submission flow, optional partial-sync boundaries.
  - Demonstrable result: a local clone or second instance can ingest content from a primary source.

- [ ] Loop 12: Anonymous posting policy modes
  - Goal: formalize unsigned, disposable-key, and temporary-identity posting modes.
  - Includes: server policy controls and API-visible behavior.
  - Demonstrable result: an operator can enable or disable anonymous posting modes predictably.

## Optional Later Slices

- [ ] Loop 13: Profile updates and display-name changes
- [x] Loop 14: Identity merge and key rotation records
- [ ] Loop 15: Raw object/debug views
- [ ] Loop 16: Derived index persistence policy
- [ ] Loop 17: Additional moderation actions such as bans
- [ ] Loop 18: Richer sync and federation tooling
- [ ] Loop 19: Alternative client surfaces beyond the main web UI

## Suggested First Three Loops

- [x] First: repository layout and canonical post format
- [x] Second: read-only thread and index rendering
- [x] Third: read-only plain-text HTTP API

These three loops would give you a demonstrable system very early:
- text-native content in git
- a local web reader
- an agent-friendly API

That gives you something real to look at before introducing signing, moderation, deletion policy, or federation complexity.
