# Canonical Records

This directory holds canonical forum records tracked in git.

For the current implementation slices, canonical forum state is still text-native and split by record family.

- `posts/` contains one canonical payload file per post.
- `identity/` contains identity bootstrap records derived from signed key-backed posting.
- `moderation/` will contain signed moderation records.

Later feature slices may add other record categories, but this loop establishes only the minimal layout needed for post storage.
