#!/usr/bin/env bash

set -euo pipefail

SERVER_URL="${FORUM_SERVER_URL:-http://127.0.0.1:8000}"
TEMP_DIRS=()

cleanup_tempdirs() {
  for tempdir in "${TEMP_DIRS[@]:-}"; do
    [[ -n "$tempdir" && -d "$tempdir" ]] && rm -rf "$tempdir"
  done
}

trap cleanup_tempdirs EXIT

usage() {
  cat <<'EOF'
Usage:
  scripts/forum_gpg.sh create-thread --key KEYID --payload FILE [--server URL] [--dry-run]
  scripts/forum_gpg.sh create-reply --key KEYID --payload FILE [--server URL] [--dry-run]
  scripts/forum_gpg.sh update-profile --key KEYID --identity-id ID --record-id ID --display-name NAME [--timestamp UTC] [--server URL] [--dry-run]
  scripts/forum_gpg.sh rotate-key --key OLDKEY --source-identity-id ID --target-key NEWKEY --record-id ID [--timestamp UTC] [--server URL] [--dry-run]
  scripts/forum_gpg.sh merge-identity --key KEYID --source-identity-id ID --target-identity-id ID --record-id ID [--note TEXT] [--timestamp UTC] [--server URL] [--dry-run]

Notes:
  - create-thread/create-reply expect a canonical ASCII payload file.
  - update-profile builds the canonical payload for Action: set_display_name.
  - rotate-key signs with the existing key and embeds the target public key in the body.
  - merge-identity signs one side of a merge assertion. Reciprocal merge records are required for the merge to become active.
  - The script prints the server's plain-text response to stdout.
EOF
}

die() {
  printf '%s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

timestamp_now() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

make_tempdir() {
  local tempdir
  tempdir="$(mktemp -d)"
  TEMP_DIRS+=("$tempdir")
  printf '%s\n' "$tempdir"
}

python_json_request() {
  local payload_file="$1"
  local signature_file="$2"
  local public_key_file="$3"
  local dry_run="$4"
  python3 - "$payload_file" "$signature_file" "$public_key_file" "$dry_run" <<'PY'
import json
import pathlib
import sys

payload_path = pathlib.Path(sys.argv[1])
signature_path = pathlib.Path(sys.argv[2])
public_key_path = pathlib.Path(sys.argv[3])
dry_run = sys.argv[4].lower() == "true"

print(json.dumps({
    "payload": payload_path.read_text(encoding="ascii"),
    "signature": signature_path.read_text(encoding="ascii"),
    "public_key": public_key_path.read_text(encoding="ascii"),
    "dry_run": dry_run,
}))
PY
}

submit_signed_payload() {
  local endpoint="$1"
  local keyid="$2"
  local payload_file="$3"
  local dry_run="$4"

  local tempdir
  tempdir="$(make_tempdir)"

  local public_key_file="$tempdir/public.asc"
  local signature_file="$tempdir/payload.asc"

  gpg --armor --export "$keyid" >"$public_key_file"
  gpg --armor --detach-sign --local-user "$keyid" --output "$signature_file" "$payload_file"

  python_json_request "$payload_file" "$signature_file" "$public_key_file" "$dry_run" \
    | curl -sS \
        -H 'Content-Type: application/json' \
        --data-binary @- \
        "$SERVER_URL$endpoint"
}

write_profile_update_payload() {
  local output_file="$1"
  local record_id="$2"
  local identity_id="$3"
  local timestamp="$4"
  local display_name="$5"

  {
    printf 'Record-ID: %s\n' "$record_id"
    printf 'Action: set_display_name\n'
    printf 'Source-Identity-ID: %s\n' "$identity_id"
    printf 'Timestamp: %s\n' "$timestamp"
    printf '\n'
    printf '%s\n' "$display_name"
  } >"$output_file"
}

write_rotate_key_payload() {
  local output_file="$1"
  local record_id="$2"
  local source_identity_id="$3"
  local target_identity_id="$4"
  local timestamp="$5"
  local target_public_key_file="$6"

  {
    printf 'Record-ID: %s\n' "$record_id"
    printf 'Action: rotate_key\n'
    printf 'Source-Identity-ID: %s\n' "$source_identity_id"
    printf 'Target-Identity-ID: %s\n' "$target_identity_id"
    printf 'Timestamp: %s\n' "$timestamp"
    printf '\n'
    cat "$target_public_key_file"
    printf '\n'
  } >"$output_file"
}

write_merge_identity_payload() {
  local output_file="$1"
  local record_id="$2"
  local source_identity_id="$3"
  local target_identity_id="$4"
  local timestamp="$5"
  local note="$6"

  {
    printf 'Record-ID: %s\n' "$record_id"
    printf 'Action: merge_identity\n'
    printf 'Source-Identity-ID: %s\n' "$source_identity_id"
    printf 'Target-Identity-ID: %s\n' "$target_identity_id"
    printf 'Timestamp: %s\n' "$timestamp"
    printf '\n'
    printf '%s\n' "$note"
  } >"$output_file"
}

extract_identity_id_from_key() {
  local key_file="$1"
  python3 - "$key_file" <<'PY'
import pathlib
import subprocess
import sys

key_path = pathlib.Path(sys.argv[1])
result = subprocess.run(
    ["gpg", "--batch", "--with-colons", "--show-keys", str(key_path)],
    check=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)
for line in result.stdout.splitlines():
    if line.startswith("fpr:"):
        fields = line.split(":")
        if len(fields) > 9 and fields[9]:
            print(f"openpgp:{fields[9].strip().lower()}")
            raise SystemExit(0)
raise SystemExit("could not derive fingerprint from target public key")
PY
}

main() {
  require_command gpg
  require_command curl
  require_command python3

  local command="${1:-}"
  if [[ -z "$command" ]]; then
    usage
    exit 1
  fi
  if [[ "$command" == "--help" || "$command" == "-h" ]]; then
    usage
    exit 0
  fi
  shift

  local keyid=""
  local payload_file=""
  local identity_id=""
  local source_identity_id=""
  local target_identity_id=""
  local target_keyid=""
  local record_id=""
  local display_name=""
  local note=""
  local timestamp=""
  local dry_run="false"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --server)
        SERVER_URL="$2"
        shift 2
        ;;
      --key)
        keyid="$2"
        shift 2
        ;;
      --payload)
        payload_file="$2"
        shift 2
        ;;
      --identity-id)
        identity_id="$2"
        shift 2
        ;;
      --source-identity-id)
        source_identity_id="$2"
        shift 2
        ;;
      --target-identity-id)
        target_identity_id="$2"
        shift 2
        ;;
      --target-key)
        target_keyid="$2"
        shift 2
        ;;
      --record-id)
        record_id="$2"
        shift 2
        ;;
      --display-name)
        display_name="$2"
        shift 2
        ;;
      --note)
        note="$2"
        shift 2
        ;;
      --timestamp)
        timestamp="$2"
        shift 2
        ;;
      --dry-run)
        dry_run="true"
        shift
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        die "unknown argument: $1"
        ;;
    esac
  done

  case "$command" in
    create-thread)
      [[ -n "$keyid" ]] || die "--key is required"
      [[ -n "$payload_file" ]] || die "--payload is required"
      [[ -f "$payload_file" ]] || die "payload file not found: $payload_file"
      submit_signed_payload "/api/create_thread" "$keyid" "$payload_file" "$dry_run"
      ;;
    create-reply)
      [[ -n "$keyid" ]] || die "--key is required"
      [[ -n "$payload_file" ]] || die "--payload is required"
      [[ -f "$payload_file" ]] || die "payload file not found: $payload_file"
      submit_signed_payload "/api/create_reply" "$keyid" "$payload_file" "$dry_run"
      ;;
    update-profile)
      [[ -n "$keyid" ]] || die "--key is required"
      [[ -n "$identity_id" ]] || die "--identity-id is required"
      [[ -n "$record_id" ]] || die "--record-id is required"
      [[ -n "$display_name" ]] || die "--display-name is required"
      [[ -n "$timestamp" ]] || timestamp="$(timestamp_now)"

      local tempdir
      tempdir="$(make_tempdir)"
      payload_file="$tempdir/profile-update.txt"
      write_profile_update_payload "$payload_file" "$record_id" "$identity_id" "$timestamp" "$display_name"
      submit_signed_payload "/api/update_profile" "$keyid" "$payload_file" "$dry_run"
      ;;
    rotate-key)
      [[ -n "$keyid" ]] || die "--key is required"
      [[ -n "$source_identity_id" ]] || die "--source-identity-id is required"
      [[ -n "$target_keyid" ]] || die "--target-key is required"
      [[ -n "$record_id" ]] || die "--record-id is required"
      [[ -n "$timestamp" ]] || timestamp="$(timestamp_now)"

      local tempdir
      tempdir="$(make_tempdir)"
      local target_public_key_file="$tempdir/target.pub.asc"
      payload_file="$tempdir/rotate-key.txt"

      gpg --armor --export "$target_keyid" >"$target_public_key_file"
      target_identity_id="$(extract_identity_id_from_key "$target_public_key_file")"
      write_rotate_key_payload \
        "$payload_file" \
        "$record_id" \
        "$source_identity_id" \
        "$target_identity_id" \
        "$timestamp" \
        "$target_public_key_file"
      submit_signed_payload "/api/link_identity" "$keyid" "$payload_file" "$dry_run"
      ;;
    merge-identity)
      [[ -n "$keyid" ]] || die "--key is required"
      [[ -n "$source_identity_id" ]] || die "--source-identity-id is required"
      [[ -n "$target_identity_id" ]] || die "--target-identity-id is required"
      [[ -n "$record_id" ]] || die "--record-id is required"
      [[ -n "$timestamp" ]] || timestamp="$(timestamp_now)"

      local tempdir
      tempdir="$(make_tempdir)"
      payload_file="$tempdir/merge-identity.txt"
      write_merge_identity_payload "$payload_file" "$record_id" "$source_identity_id" "$target_identity_id" "$timestamp" "$note"
      submit_signed_payload "/api/link_identity" "$keyid" "$payload_file" "$dry_run"
      ;;
    *)
      usage
      die "unknown command: $command"
      ;;
  esac
}

main "$@"
