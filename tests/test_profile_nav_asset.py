from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


class ProfileNavAssetTests(unittest.TestCase):
    def run_node(self, script: str) -> str:
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", script],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    def test_profile_nav_asset_derives_profile_href_from_public_key(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_nav.js").as_uri()
        vendor_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        script = f"""
import fs from "node:fs/promises";
import * as openpgp from {json.dumps(vendor_url)};
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewrittenAssetSource = assetSource.replace(
  './vendor/openpgp.min.mjs',
  {json.dumps(vendor_url)},
);
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenAssetSource).toString("base64")}}`;
const {{ profileHrefFromPublicKey }} = await import(assetModuleUrl);

const generated = await openpgp.generateKey({{
  type: "ecc",
  curve: "ed25519",
  userIDs: [{{ name: "Profile Nav Test" }}],
  format: "armored",
}});
const publicKey = await openpgp.readKey({{ armoredKey: generated.publicKey }});
const fingerprint = publicKey.getFingerprint().toLowerCase();
const href = await profileHrefFromPublicKey(generated.publicKey);
process.stdout.write(JSON.stringify({{ href, fingerprint }}));
"""
        payload = json.loads(self.run_node(script))

        self.assertEqual(payload["href"], f"/profiles/openpgp-{payload['fingerprint']}")


if __name__ == "__main__":
    unittest.main()
