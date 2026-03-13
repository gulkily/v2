# Forum Architecture Responses Summary

## Confirmed Decisions

### Data Model
- The forum uses a flat global thread space with board tags rather than boards as hard containers.
- The canonical storage unit is one file per post.
- Each post is a plain text record with header fields plus body.
- Posts are ASCII-only and support only a tiny markup subset, quoting, and links.
- UI should primarily present linear threads, while the data model also supports quoted cross-links.

### Content Lifecycle
- Edits should be represented as follow-up records rather than in-place mutation.
- Deletion is allowed, including routine scheduled deletion of unpinned posts.
- Public instances should support immediate soft-deletes in live state.
- Sensitive content may later be removed from the repository and rewritten out of history, and the system must tolerate that loss.
- Ephemerality is a deliberate product property inspired by 4chan.

### Identity And Auth
- PKI stays minimal: use OpenPGP mainly for key generation and signing, with identity semantics built at the application layer.
- Display names are customizable.
- Multiple public keys can be merged into one logical identity.
- Key rotation and invalidation happen through signed links between keys.
- Identity is bootstrapped by posting a public key, and later profile changes are signed updates tied to that identity.
- Anonymous posting is allowed if an instance permits it.
- Moderation actions should be signed and stored in git.
- Servers may reject valid signed content for local policy reasons.

### Federation And Sync
- The system is intentionally loose and forkable: many repos may mirror and merge each other.
- Divergent forks are legitimate and do not need to reconverge.
- Git is the canonical sync mechanism.
- HTTP is also required for clients that cannot use git.
- Partial sync may be supported, but full clone is also acceptable initially.

### API And Execution Model
- The HTTP API should use a very simple plain text, line-based format.
- Clients sign a canonical normalized representation, not necessarily the exact transport payload.
- Browser-generated keys stored in local storage are the initial browser key model.
- The backend writes commits directly.

### Backend Portability
- The backend contract should be a fixed set of scripts with well-defined input and output formats.
- Multiple implementations are expected to run against the same repo state.
- Equivalent implementations must produce byte-identical output for identical input and repository state.
- Initial reference implementations should be in Perl and Python with a simple CGI interface and minimal dependencies.
- Perl target: attempt compatibility with 5.10.
- Python target: attempt compatibility with 3.8 through 3.15.

### Initial Product Scope
- Initial read surfaces: board index, thread view, post permalink, user/profile view, moderation log.
- Raw object view can wait.
- Initial write surfaces: new thread and reply only.
- The first version is chronological and thread-centric, with no voting or ranking.
- Reddit-like loose categorization, 4chan-like ephemerality, and HN-like focus on quality discussion are core inspirations.
- Karma systems, ranking algorithms, and exact legacy UIs are out of scope.

## Implications And Tensions

- "One file per post" and "a plain text file is a valid post" pull against the need for stable metadata such as thread membership, authorship, signature, and moderation state. If file contents stay optional, some metadata likely needs to live in filenames, paths, or companion records.
- Deletion now has two required modes: immediate soft-delete for public operation and optional hard purge for sensitive data. Read paths and indexes need explicit behavior when referenced payloads no longer exist.
- Identity creation by posting a public key is defined, but the first-version write surface excludes explicit key registration and profile update flows.
- Byte-identical output across Perl and Python requires strict canonicalization rules for sorting, timestamps, whitespace, header ordering, line endings, escaping, and error handling.
- Anonymous posting is allowed per instance, but the relationship between anonymous posts and signed/authenticated posts is still underspecified.
- Fork-friendly federation is clear philosophically, but cross-instance identifiers and reference stability are not yet defined.

## Follow-Up Questions

1. If a plain text file can be a valid post with no mandatory metadata, where do thread ID, board tags, timestamps, author references, and signatures live? A: Based on hashes, file paths, companion index files, or some combination.
2. Do you want header fields inside each post file to be optional, recommended, or mandatory for network-visible posts? A: Optional, but recommended for better interoperability and client behavior.
3. What is the canonical post ID: git blob hash, commit hash plus path, content hash, signed payload hash, or a separate generated ID? A: Content hash or signed payload hash is likely, to allow for stable references even if the file moves or is rewritten.
4. How is a thread identified in the flat global space: by the first post's ID, by a thread tag, or by a separate thread record? A: By the first post's ID, with thread membership inferred from reply relationships and possibly reinforced by thread tags.
5. Should board tags live inside the post header, in the file path, in companion index files, or in all of the above? A: Possibly all of the above, with file paths and headers providing redundancy and indexes for efficient querying.
6. What exactly does deletion mean:
   - remove from current branch only Y
   - keep a tombstone record Y
   - rewrite history Y
   - prune via periodic repo compaction Y
   - immediate public soft-delete Y
   - later sensitive-content hard purge Y
7. How should pinned posts be represented, and who is allowed to pin or unpin them? A: By thread ID reference.
8. If edits are follow-up records, what record type expresses a correction, and how should the UI render the relationship? A: Let's scope edits out of the first version.
9. How does a user prove that two keys belong to one identity: mutual signatures, a signed merge record, or some other application-level claim? A: A signed merge record that references both keys and asserts their relationship to the same identity. (Using our own simple format referencing the full fingerprint ID, not using PGP's format.)
10. Who is allowed to merge keys into one identity: the current key holder only, both old and new keys, or moderators as well? A: Moderators as well, but each instance gets to decide whether to trust moderator assertions about identity merges. 
11. For anonymous posting, do you mean:
   - unsigned posts Y
   - one-off disposable signed keys with no profile Y
   - server-issued temporary identities Y
12. If a server may reject content arbitrarily, do you want the rejection reason exposed in the API, and should it be machine-readable? A: Optional.
13. What is the minimum HTTP API surface for version 1: `create_thread`, `create_reply`, `list_index`, `get_thread`, `get_post`, `get_profile`, `get_moderation_log`? A: Sounds good.
14. What is the exact line-based wire format for requests and responses, including multiline bodies and errors? A: This should be made into a new spec document draft, please.
15. What exact canonical representation gets signed: headers plus body, a normalized field list, or a detached canonical envelope? A: Put it into the spec document, please.
16. How should timestamps be generated and normalized so Perl and Python implementations remain byte-identical? A: Use ISO 8601 format in UTC, generated at the time of post creation, and included in the signed content. For edits and moderation actions, use the same timestamp format and include it in the signed content as well.
17. What newline convention is canonical: LF only, always trailing newline, and fixed header ordering? A: LF only, always trailing newline, no defined header ordering, but headers must be contiguous at the top of the file and separated from the body by a blank line. Headers should be in "Key: Value" format, with keys being case-insensitive and values trimmed of leading and trailing whitespace. The exact header set is flexible, but should include at least "Author", "Timestamp", "Thread-ID", and "Board-Tags" for posts.
18. Should implementations be required to produce byte-identical success output only, or also byte-identical error output? A: Byte-identical success output is required. Error output should be consistent in format but does not need to be byte-identical, as long as it follows the defined error response structure in the spec document.
19. Since initial write surfaces exclude key registration and profile update, how does a browser user establish identity in version 1 before posting? A: Generate key pair, post public key as the first post in a thread, and use that as the identity bootstrap. Profile updates can be implemented as follow-up posts that reference the initial key post, but this can be scoped out of version 1 for simplicity.
20. Do you want a formal repository layout now, such as directories for posts, profiles, moderation actions, indexes, and derived caches? Yes, please include that in a second spec document.
