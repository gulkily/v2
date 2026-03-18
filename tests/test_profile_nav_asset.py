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

    def test_profile_nav_asset_counts_merge_notifications_from_summary_text(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_nav.js").as_uri()
        vendor_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        script = f"""
import fs from "node:fs/promises";
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewrittenAssetSource = assetSource.replace(
  './vendor/openpgp.min.mjs',
  {json.dumps(vendor_url)},
);
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenAssetSource).toString("base64")}}`;
const {{ mergeNotificationCount }} = await import(assetModuleUrl);

const summaryText = [
  "Command: get_merge_management",
  "Identity-ID: openpgp:test",
  "Historical-Match-Count: 2",
  "Outgoing-Request-Count: 1",
  "Incoming-Request-Count: 3",
  "Dismissed-Request-Count: 0",
  "Approved-Request-Count: 0",
].join("\\n");
process.stdout.write(JSON.stringify({{ count: mergeNotificationCount(summaryText) }}));
"""
        payload = json.loads(self.run_node(script))

        self.assertEqual(payload["count"], 5)

    def test_profile_nav_asset_points_nav_to_merge_page_when_notifications_exist(self) -> None:
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
const {{ enhanceProfileNav }} = await import(assetModuleUrl);

const generated = await openpgp.generateKey({{
  type: "ecc",
  curve: "ed25519",
  userIDs: [{{ name: "Profile Nav Test" }}],
  format: "armored",
}});
const publicKey = await openpgp.readKey({{ armoredKey: generated.publicKey }});
const fingerprint = publicKey.getFingerprint().toLowerCase();
const navLink = {{
  hidden: true,
  textContent: "My profile",
  setAttribute(name, value) {{
    this[name] = value;
  }},
}};
const doc = {{
  querySelector(selector) {{
    return selector === "[data-profile-nav-link]" ? navLink : null;
  }},
}};
const storage = {{
  getItem(key) {{
    return key === "forum_public_key_armored" ? generated.publicKey : "";
  }},
}};
const fetchImpl = async () => ({{
  ok: true,
  async text() {{
    return [
      "Command: get_merge_management",
      "Identity-ID: openpgp:test",
      "Historical-Match-Count: 1",
      "Outgoing-Request-Count: 0",
      "Incoming-Request-Count: 2",
      "Dismissed-Request-Count: 0",
      "Approved-Request-Count: 0",
    ].join("\\n");
  }},
}});

await enhanceProfileNav(doc, storage, fetchImpl);
process.stdout.write(JSON.stringify({{
  hidden: navLink.hidden,
  href: navLink.href,
  textContent: navLink.textContent,
  fingerprint,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertFalse(payload["hidden"])
        self.assertEqual(payload["href"], f"/profiles/openpgp-{payload['fingerprint']}/merge")
        self.assertEqual(payload["textContent"], "My profile (3)")


if __name__ == "__main__":
    unittest.main()
