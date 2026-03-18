from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from forum_core.identity import fingerprint_from_public_key_text
from forum_core.public_keys import (
    fingerprint_from_signature_path,
    resolve_canonical_public_key_path,
    resolve_public_key_from_signature,
    store_or_reuse_public_key,
)


class PublicKeyStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tempdir.name)
        self.openpgp_module_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        self.user_keys = self.generate_signing_keypair("Public Key Store Test")

    def tearDown(self) -> None:
        self.repo_tempdir.cleanup()

    def run_command(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

    def run_node_module(self, script: str) -> str:
        result = self.run_command(["node", "--input-type=module", "--eval", script])
        return result.stdout

    def generate_signing_keypair(self, name: str) -> dict[str, str]:
        script = f"""
import * as openpgp from {json.dumps(self.openpgp_module_url)};
const generated = await openpgp.generateKey({{
  type: "ecc",
  curve: "ed25519",
  userIDs: [{{ name: {json.dumps(name)} }}],
  format: "armored",
}});
process.stdout.write(JSON.stringify({{
  privateKey: generated.privateKey,
  publicKey: generated.publicKey,
}}));
"""
        return json.loads(self.run_node_module(script))

    def sign_payload(self, payload_text: str) -> str:
        script = f"""
import * as openpgp from {json.dumps(self.openpgp_module_url)};
const privateKey = await openpgp.readPrivateKey({{
  armoredKey: {json.dumps(self.user_keys["privateKey"])},
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
        return self.run_node_module(script)

    def test_store_or_reuse_public_key_uses_one_canonical_path(self) -> None:
        first = store_or_reuse_public_key(repo_root=self.repo_root, public_key_text=self.user_keys["publicKey"])
        second = store_or_reuse_public_key(repo_root=self.repo_root, public_key_text=self.user_keys["publicKey"])

        fingerprint = fingerprint_from_public_key_text(self.user_keys["publicKey"])
        expected_path = resolve_canonical_public_key_path(self.repo_root, fingerprint)

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.path, expected_path)
        self.assertEqual(second.path, expected_path)
        self.assertEqual(expected_path.read_text(encoding="ascii"), self.user_keys["publicKey"])

    def test_signature_fingerprint_resolves_to_canonical_public_key(self) -> None:
        stored_key = store_or_reuse_public_key(repo_root=self.repo_root, public_key_text=self.user_keys["publicKey"])
        signature_path = self.repo_root / "sample.asc"
        signature_path.write_text(self.sign_payload("hello"), encoding="ascii")

        self.assertEqual(fingerprint_from_signature_path(signature_path), stored_key.fingerprint)
        self.assertEqual(
            resolve_public_key_from_signature(repo_root=self.repo_root, signature_path=signature_path),
            stored_key.path,
        )
