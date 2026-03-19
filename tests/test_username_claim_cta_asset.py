from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


class UsernameClaimCtaAssetTests(unittest.TestCase):
    def run_node(self, script: str) -> str:
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", script],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    def test_username_claim_cta_asset_parses_eligible_response(self) -> None:
        asset_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "username_claim_cta.js"
        ).as_uri()
        profile_nav_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_nav.js"
        ).as_uri()
        loader_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "openpgp_loader.js"
        ).as_uri()
        vendor_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        script = f"""
import fs from "node:fs/promises";
const loaderSource = await fs.readFile(new URL({json.dumps(loader_url)}), "utf8");
const rewrittenLoaderSource = loaderSource.replace(
  "./vendor/openpgp.min.mjs",
  {json.dumps(vendor_url)},
);
const loaderModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenLoaderSource).toString("base64")}}`;
const profileNavSource = await fs.readFile(new URL({json.dumps(profile_nav_url)}), "utf8");
const rewrittenProfileNavSource = profileNavSource.replace(
  "./openpgp_loader.js",
  loaderModuleUrl,
);
const profileNavModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenProfileNavSource).toString("base64")}}`;
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewrittenAssetSource = assetSource.replace(
  "./profile_nav.js",
  profileNavModuleUrl,
);
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenAssetSource).toString("base64")}}`;
const {{ usernameClaimCtaStateForIdentity }} = await import(assetModuleUrl);

const state = await usernameClaimCtaStateForIdentity("openpgp:alpha", async () => ({{
  ok: true,
  async text() {{
    return [
      "Command: get_username_claim_cta",
      "Identity-ID: openpgp:alpha",
      "Can-Claim-Username: yes",
      "Update-Href: /profiles/openpgp-alpha/update",
    ].join("\\n");
  }},
}}));

process.stdout.write(JSON.stringify(state));
"""
        payload = json.loads(self.run_node(script))

        self.assertEqual(
            payload,
            {
                "canClaimUsername": True,
                "updateHref": "/profiles/openpgp-alpha/update",
            },
        )

    def test_username_claim_cta_asset_reveals_banner_for_eligible_stored_key(self) -> None:
        asset_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "username_claim_cta.js"
        ).as_uri()
        profile_nav_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_nav.js"
        ).as_uri()
        loader_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "openpgp_loader.js"
        ).as_uri()
        vendor_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        script = f"""
import fs from "node:fs/promises";
import * as openpgp from {json.dumps(vendor_url)};
const loaderSource = await fs.readFile(new URL({json.dumps(loader_url)}), "utf8");
const rewrittenLoaderSource = loaderSource.replace(
  "./vendor/openpgp.min.mjs",
  {json.dumps(vendor_url)},
);
const loaderModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenLoaderSource).toString("base64")}}`;
const profileNavSource = await fs.readFile(new URL({json.dumps(profile_nav_url)}), "utf8");
const rewrittenProfileNavSource = profileNavSource.replace(
  "./openpgp_loader.js",
  loaderModuleUrl,
);
const profileNavModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenProfileNavSource).toString("base64")}}`;
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewrittenAssetSource = assetSource.replace(
  "./profile_nav.js",
  profileNavModuleUrl,
);
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenAssetSource).toString("base64")}}`;
const {{ enhanceUsernameClaimCta }} = await import(assetModuleUrl);

const generated = await openpgp.generateKey({{
  type: "ecc",
  curve: "ed25519",
  userIDs: [{{ name: "Username CTA Test" }}],
  format: "armored",
}});
const link = {{
  href: "",
  setAttribute(name, value) {{
    this[name] = value;
  }},
}};
const root = {{
  hidden: true,
  querySelector(selector) {{
    return selector === "[data-username-claim-link]" ? link : null;
  }},
}};
const doc = {{
  querySelector(selector) {{
    return selector === "[data-username-claim-cta]" ? root : null;
  }},
}};
const storage = {{
  getItem(key) {{
    return key === "forum_public_key_armored" ? generated.publicKey : "";
  }},
}};
const fetchImpl = async (url) => ({{
  ok: true,
  async text() {{
    return [
      "Command: get_username_claim_cta",
      "Identity-ID: derived",
      "Can-Claim-Username: yes",
      "Update-Href: /profiles/openpgp-derived/update",
    ].join("\\n");
  }},
}});

await enhanceUsernameClaimCta(doc, storage, fetchImpl);
process.stdout.write(JSON.stringify({{
  hidden: root.hidden,
  href: link.href,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertFalse(payload["hidden"])
        self.assertEqual(payload["href"], "/profiles/openpgp-derived/update")

    def test_username_claim_cta_asset_keeps_banner_hidden_for_ineligible_response(self) -> None:
        asset_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "username_claim_cta.js"
        ).as_uri()
        profile_nav_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_nav.js"
        ).as_uri()
        loader_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "openpgp_loader.js"
        ).as_uri()
        vendor_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        script = f"""
import fs from "node:fs/promises";
import * as openpgp from {json.dumps(vendor_url)};
const loaderSource = await fs.readFile(new URL({json.dumps(loader_url)}), "utf8");
const rewrittenLoaderSource = loaderSource.replace(
  "./vendor/openpgp.min.mjs",
  {json.dumps(vendor_url)},
);
const loaderModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenLoaderSource).toString("base64")}}`;
const profileNavSource = await fs.readFile(new URL({json.dumps(profile_nav_url)}), "utf8");
const rewrittenProfileNavSource = profileNavSource.replace(
  "./openpgp_loader.js",
  loaderModuleUrl,
);
const profileNavModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenProfileNavSource).toString("base64")}}`;
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewrittenAssetSource = assetSource.replace(
  "./profile_nav.js",
  profileNavModuleUrl,
);
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenAssetSource).toString("base64")}}`;
const {{ enhanceUsernameClaimCta }} = await import(assetModuleUrl);

const generated = await openpgp.generateKey({{
  type: "ecc",
  curve: "ed25519",
  userIDs: [{{ name: "Username CTA Test" }}],
  format: "armored",
}});
const link = {{
  href: "",
  setAttribute(name, value) {{
    this[name] = value;
  }},
}};
const root = {{
  hidden: true,
  querySelector(selector) {{
    return selector === "[data-username-claim-link]" ? link : null;
  }},
}};
const doc = {{
  querySelector(selector) {{
    return selector === "[data-username-claim-cta]" ? root : null;
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
      "Command: get_username_claim_cta",
      "Identity-ID: derived",
      "Can-Claim-Username: no",
    ].join("\\n");
  }},
}});

await enhanceUsernameClaimCta(doc, storage, fetchImpl);
process.stdout.write(JSON.stringify({{
  hidden: root.hidden,
  href: link.href,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertTrue(payload["hidden"])
        self.assertEqual(payload["href"], "")


if __name__ == "__main__":
    unittest.main()
