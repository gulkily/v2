from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from forum_cgi.posting import PostingError, ensure_ascii_text


def verify_detached_signature(
    *,
    payload_text: str,
    signature_text: str,
    public_key_text: str,
) -> str:
    payload_text = ensure_ascii_text(payload_text, field_name="payload")
    signature_text = ensure_ascii_text(signature_text, field_name="signature")
    public_key_text = ensure_ascii_text(public_key_text, field_name="public_key")

    with tempfile.TemporaryDirectory(prefix="forum-gpg-", dir="/tmp") as tempdir:
        temp_path = Path(tempdir)
        homedir = temp_path / "gnupg-home"
        homedir.mkdir(mode=0o700)

        public_key_path = temp_path / "public.asc"
        signature_path = temp_path / "payload.asc"
        payload_path = temp_path / "payload.txt"
        public_key_path.write_text(public_key_text, encoding="ascii")
        signature_path.write_text(signature_text, encoding="ascii")
        payload_path.write_text(payload_text, encoding="ascii")

        import_result = subprocess.run(
            [
                "gpg",
                "--homedir",
                str(homedir),
                "--batch",
                "--status-fd",
                "1",
                "--import",
                str(public_key_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        import_ok = any(line.startswith("[GNUPG:] IMPORT_OK ") for line in import_result.stdout.splitlines())
        if import_result.returncode != 0 and not import_ok:
            raise PostingError("bad_request", "public_key could not be imported")

        verify_result = subprocess.run(
            [
                "gpg",
                "--homedir",
                str(homedir),
                "--batch",
                "--status-fd",
                "1",
                "--verify",
                str(signature_path),
                str(payload_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if verify_result.returncode != 0:
            raise PostingError("bad_request", "signature verification failed")

        for line in verify_result.stdout.splitlines():
            if line.startswith("[GNUPG:] VALIDSIG "):
                parts = line.split()
                if len(parts) >= 3:
                    return parts[2]

    raise PostingError("bad_request", "signature verification did not yield a signer fingerprint")


def sign_detached_payload(
    *,
    payload_text: str,
    private_key_text: str,
) -> str:
    payload_text = ensure_ascii_text(payload_text, field_name="payload")
    private_key_text = ensure_ascii_text(private_key_text, field_name="private_key")
    openpgp_module_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs").as_uri()
    script = f"""
import * as openpgp from {json.dumps(openpgp_module_url)};
const privateKey = await openpgp.readPrivateKey({{
  armoredKey: {json.dumps(private_key_text)},
}});
const message = await openpgp.createMessage({{
  text: {json.dumps(payload_text)},
}});
const signature = await openpgp.sign({{
  message,
  signingKeys: privateKey,
  detached: true,
  format: "armored",
}});
process.stdout.write(signature);
"""
    result = subprocess.run(
        [
            "node",
            "--input-type=module",
            "--eval",
            script,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise PostingError("bad_request", "payload signing failed")
    return ensure_ascii_text(result.stdout, field_name="signature")
