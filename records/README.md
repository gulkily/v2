# Canonical Records

This directory holds canonical forum records tracked in git.

For the current implementation slices, canonical forum state is still text-native and split by record family.

- `posts/` contains one canonical payload file per post.
  Typed root threads such as `Thread-Type: task` also live here; for task threads, the
  root post carries the current task metadata and replies remain the comment flow.
- `identity/` contains identity bootstrap records derived from signed key-backed posting.
- `identity-links/` contains signed merge and key-rotation records that resolve multiple keys or identities into one logical profile.
- `profile-updates/` contains signed profile-metadata updates such as display-name changes for resolved identities.
- `moderation/` contains signed moderation records.

Later feature slices may add other record categories, but this loop establishes only the minimal layout needed for post storage.
