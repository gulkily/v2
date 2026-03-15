# GPG CLI Workflow

Use [`../scripts/forum_gpg.sh`](../scripts/forum_gpg.sh) to sign canonical payloads with your own local `gpg` key and submit them to the forum API.

## Prerequisites

1. Start the local forum server with `./forum start`.
2. Make sure `gpg`, `curl`, and `python3` are installed.
3. Make sure your signing key already exists in your local GPG keyring.

The helper script defaults to `http://127.0.0.1:8000`. Override it with `--server URL` or `FORUM_SERVER_URL`.

## Bootstrap a new profile from your own key

Identity bootstrap happens automatically on your first signed post. There is no separate registration step. The server verifies your detached signature, derives `Identity-ID: openpgp:<fingerprint>`, and writes the bootstrap record under `records/identity/`.

Create a canonical thread payload:

```text
Post-ID: thread-20260315-my-first-signed-post
Board-Tags: general
Subject: First signed post

Bootstrapping my forum profile from my own GPG key.
```

Save that as `thread.txt`, then submit it:

```bash
scripts/forum_gpg.sh create-thread \
  --key YOURKEYID \
  --payload thread.txt
```

The response includes:

- `Identity-ID: openpgp:<fingerprint>`
- `Identity-Bootstrap-Path: records/identity/identity-openpgp-<fingerprint>.txt`
- `Identity-Bootstrap-Created: yes`

Read back the profile:

```bash
curl -sS "http://127.0.0.1:8000/api/get_profile?identity_id=openpgp:<fingerprint>"
```

## Sign later posts with the same key

Create another canonical post payload and submit it with the same key:

```bash
scripts/forum_gpg.sh create-reply \
  --key YOURKEYID \
  --payload reply.txt
```

If the key already has a bootstrap record, the response will show `Identity-Bootstrap-Created: no`.

## Set or change your display name

After the profile exists, publish a signed profile update:

```bash
scripts/forum_gpg.sh update-profile \
  --key YOURKEYID \
  --identity-id openpgp:<fingerprint> \
  --record-id profile-update-20260315-your-name \
  --display-name yourname
```

The helper generates the canonical payload for `Action: set_display_name` and submits it to `/api/update_profile`.

## Rotate to a new signing key while keeping the same profile

Use `rotate_key` when you control an existing visible identity and want to introduce a new key that is not visible yet.

1. Keep the old key available locally.
2. Import or generate the new key locally.
3. Submit the rotation record signed by the old key:

```bash
scripts/forum_gpg.sh rotate-key \
  --key OLDKEYID \
  --source-identity-id openpgp:<old-fingerprint> \
  --target-key NEWKEYID \
  --record-id rotate-key-20260315-old-to-new
```

This publishes a signed `rotate_key` record whose body is the new key's ASCII-armored public key.

4. Make the new key visible by submitting a signed post with it:

```bash
scripts/forum_gpg.sh create-thread \
  --key NEWKEYID \
  --payload new-key-thread.txt
```

That first signed post from the new key will bootstrap `openpgp:<new-fingerprint>`. The identity resolution layer will then treat the old and new keys as one logical profile.

## Merge two already-visible profiles

Use `merge_identity` when both identities are already visible and should resolve to one profile.

Important: one merge record is not enough. The merge only becomes active when reciprocal records exist from both sides.

First assertion, signed by identity A:

```bash
scripts/forum_gpg.sh merge-identity \
  --key KEY_A \
  --source-identity-id openpgp:<fingerprint-a> \
  --target-identity-id openpgp:<fingerprint-b> \
  --record-id merge-20260315-a-to-b \
  --note "same operator"
```

Reciprocal assertion, signed by identity B:

```bash
scripts/forum_gpg.sh merge-identity \
  --key KEY_B \
  --source-identity-id openpgp:<fingerprint-b> \
  --target-identity-id openpgp:<fingerprint-a> \
  --record-id merge-20260315-b-to-a \
  --note "same operator"
```

After both records exist, profile reads will resolve the identities into one canonical profile.

## Dry-run previews

Each subcommand supports `--dry-run`. The server will validate the signature and payload and return the intended storage paths without committing the record.

Example:

```bash
scripts/forum_gpg.sh update-profile \
  --key YOURKEYID \
  --identity-id openpgp:<fingerprint> \
  --record-id profile-update-preview \
  --display-name yourname \
  --dry-run
```
