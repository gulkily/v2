# Forum Architecture Questions

Write your answers under each question.

## 1. Content Model

1. Are `boards` the primary top-level container, or do you want a flatter global thread space with board tags?
Response: Flat thread space, board tags.

2. What is the canonical unit of storage: one file per post, one file per thread, append-only log files, or a mix?
Response: One file per post.

3. Should every object type be a plain text record with header fields plus body, or do you want an even simpler custom line format?
Response: Plain text record with header fields plus body.

4. What metadata is mandatory for a post: author key ID, timestamp, board, thread ID, parent ID, subject, body, signature?
Response: No metadata is mandatory, a plain textfile is a valid post.

5. Should edits be allowed, or should all posts be immutable with corrections represented as follow-up records?
Response: Corrections as follow-up records, deletions allowed.

6. Should deletions be impossible at the data layer, with moderation represented as signed hide or tombstone actions instead?
Response: Deletion is allowed. Also, as per 4chan inspiration, posts can be regularly deleted on a schedule, unless pinned.

7. Do you want replies to form strict trees, or should the data model support both linear threads and quoted cross-links?
Response: Quoted cross-links, but the UI should primarily surface linear threads.

## 2. Identity And Auth

8. Do you want display names to be tied to keys permanently, or should one key be able to present multiple personas?
Response: Display names customizable, and also keys are semi-disposable, and multiple public keys can be merged into one identity. Use as little PGP infrastructure as possible, basically just keygen and signing, and build the identity system on top of that.

9. How should key rotation work when a user wants to replace a compromised or expired OpenPGP key?
Response: Keys are linked logically by referencing from each other. Keys can be invalidated post-fact.

10. Should a new identity be created by the first signed post, or do you want a separate signed profile registration flow?
Response: The identity should be created by posting the public key, which also has default username. Username can later be changed by signing a profile update referencing the same key.

11. Do you want anonymous posting at all, and if so, how do you want that to coexist with PKI-backed authorship?
Response: Anonymous posting is allowed per-instance, depending on server policy.

12. Should moderators also act via signed records stored in git, so bans, locks, and hides are fully auditable?
Response: Yes, moderation actions should be signed and stored in git.

13. Is the server allowed to reject content for local policy reasons even if the signature and format are valid?
Response: Yes, arbitrarily.

## 3. Federation And Sync

14. Do you want a single canonical repo per instance, or do you expect many repos that can mirror and merge each other?
Response: As loose and freeform as possible while still being usable, so many repos that can mirror and merge each other.

15. When two instances diverge, is conflict resolution meant to be pure git, application-level reconciliation, or "forks are legitimate and need not converge"?
Response: Forks are legitimate and need not converge.

16. Should sync happen primarily through `git fetch` and `git push`, through an HTTP sync API, or both equally?
Response: Both equally, with git as the canonical sync mechanism but an HTTP API for clients that can't do git.

17. Do you want partial sync by board or thread, or is cloning the full repository acceptable for the first version?
Response: Either or.

## 4. API And Signing

18. Should the API be JSON over HTTP, plain text over HTTP, or an ASCII-constrained JSON protocol?
Response: Plain text over HTTP, with a very simple line-based format for both requests and responses.

19. Do you want the browser client to sign the exact payload sent to the server, or a canonical normalized representation derived from it?
Response: A canonical normalized representation derived from it, to allow for more flexible client-side composition and formatting while keeping the signed content stable.

20. Where should browser-held private keys live: imported armored keys in local storage, session-only keys, hardware tokens, or something else?
Response: Locally generated keys stored in local storage. Other options can be added later, but this is the most universally accessible starting point.

21. Should the backend write commits directly, or should it emit proposed changes that another process validates and commits?
Response: Write commits directly.

## 5. Backend Contract

22. For the CGI-like backend contract, do you want a fixed set of scripts such as `create_post`, `list_threads`, `get_thread`, `moderate`, and `sync`?
Response: Yes, a fixed set of scripts with well-defined input and output formats.

23. When you say multiple implementations may be called selectively or randomly, is the goal redundancy, experimentation, verification, or load distribution?
Response: Redundancy, verification, and experimentation. The idea is that multiple implementations should be able to run against the same repository state and produce the same visible forum state, so they can be used interchangeably for reliability and also to test new implementations against a known reference.

24. Should two different backend implementations be required to produce byte-identical output for the same repository state?
Response: Yes, for the same repository state and the same input, they should produce byte-identical output. This is important for verification and redundancy.

25. Do you want a reference implementation first in shell or CGI for maximal portability, or in a more structured language with CGI compatibility?
Response: A reference implementation in Perl and Python, with a very simple CGI interface, and minimal third-party module use. In Perl, attempt compatibility with 5.10. In Python, attempt backwards compatibility with 3.8-3.15. The goal is to have something that can run in the most minimal environments, but also be clear and maintainable enough to serve as a reference for more structured implementations later.

## 6. Product Scope

26. What are the initial read surfaces: board index, thread view, post permalink, user or profile view, moderation log, raw object view?
Response: Board index, thread view, post permalink, user or profile view, moderation log. Raw object view can be added later as a debugging tool.

27. What are the initial write surfaces: new thread, reply, edit, hide, lock, ban, key registration, profile update?
Response: Just new thread and reply for the first version, to keep the scope manageable. Edits, hides, locks, bans, key registration, and profile updates can be added in later iterations.

28. Do you want voting or ranking at all, or should the first version stay chronological and thread-centric?
Response: The first version should stay chronological and thread-centric, without voting or ranking. The focus is on building a solid foundation for the content model, identity, and sync mechanisms first. Voting and ranking can be considered in future iterations once the core system is stable.

29. Which parts of HN, Reddit, and 4chan are actually essential to preserve, and which parts are explicitly out of scope?
Response:
For Reddit: the idea of subreddits as a loose categorization mechanism is worth preserving, but the karma system and voting mechanics are out of scope. The threaded conversation model is also worth preserving, but the specific UI and ranking algorithms are not.
For 4chan: the ephemeral nature of posts and the ability to delete them is worth preserving, as well as the flat thread structure with cross-linking. The specific culture and content norms of 4chan are not essential to preserve, and the UI can be more modern and user-friendly.
For HN: the focus on high-quality content and discussions is worth preserving, but the specific ranking algorithm and the emphasis on tech news are not essential. The threaded conversation model is also worth preserving, but the UI can be more flexible and less minimalist than HN's.

30. Do you want rich text at all, or should posts be plain ASCII with only quoting, links, and maybe a tiny markup subset?
Response: Posts should be plain ASCII with only quoting, links, and a tiny markup subset (like * for emphasis and > for quotes). The focus is on keeping the content human-readable in its raw form, without requiring rendering to understand it. Rich text features can be considered in future iterations if there's demand, but the initial version should prioritize simplicity and readability.
