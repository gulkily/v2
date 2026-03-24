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
const loaderSource = await fs.readFile(new URL({json.dumps((Path(__file__).resolve().parent.parent / "templates" / "assets" / "openpgp_loader.js").as_uri())}), "utf8");
const rewrittenLoaderSource = loaderSource.replace(
  "./vendor/openpgp.min.mjs",
  {json.dumps(vendor_url)},
);
const loaderModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenLoaderSource).toString("base64")}}`;
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewrittenAssetSource = assetSource.replace(
  "./openpgp_loader.js",
  loaderModuleUrl,
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
const loaderSource = await fs.readFile(new URL({json.dumps((Path(__file__).resolve().parent.parent / "templates" / "assets" / "openpgp_loader.js").as_uri())}), "utf8");
const rewrittenLoaderSource = loaderSource.replace(
  "./vendor/openpgp.min.mjs",
  {json.dumps(vendor_url)},
);
const loaderModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenLoaderSource).toString("base64")}}`;
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewrittenAssetSource = assetSource.replace(
  "./openpgp_loader.js",
  loaderModuleUrl,
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

    def test_profile_nav_asset_extracts_fingerprint_from_identity_id(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_nav.js").as_uri()
        vendor_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        script = f"""
import fs from "node:fs/promises";
const loaderSource = await fs.readFile(new URL({json.dumps((Path(__file__).resolve().parent.parent / "templates" / "assets" / "openpgp_loader.js").as_uri())}), "utf8");
const rewrittenLoaderSource = loaderSource.replace(
  "./vendor/openpgp.min.mjs",
  {json.dumps(vendor_url)},
);
const loaderModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenLoaderSource).toString("base64")}}`;
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewrittenAssetSource = assetSource.replace(
  "./openpgp_loader.js",
  loaderModuleUrl,
);
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenAssetSource).toString("base64")}}`;
const {{ fingerprintFromIdentityId }} = await import(assetModuleUrl);

process.stdout.write(JSON.stringify({{
  fingerprint: fingerprintFromIdentityId("openpgp:abcd1234ef"),
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertEqual(payload["fingerprint"], "abcd1234ef")

    def test_profile_nav_asset_points_nav_to_merge_page_when_notifications_exist(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_nav.js").as_uri()
        vendor_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        script = f"""
import fs from "node:fs/promises";
import * as openpgp from {json.dumps(vendor_url)};
const loaderSource = await fs.readFile(new URL({json.dumps((Path(__file__).resolve().parent.parent / "templates" / "assets" / "openpgp_loader.js").as_uri())}), "utf8");
const rewrittenLoaderSource = loaderSource.replace(
  "./vendor/openpgp.min.mjs",
  {json.dumps(vendor_url)},
);
const loaderModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenLoaderSource).toString("base64")}}`;
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewrittenAssetSource = assetSource.replace(
  "./openpgp_loader.js",
  loaderModuleUrl,
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
  attributes: {{}},
  "data-merge-feature-enabled": "1",
  textContent: "My profile",
  setAttribute(name, value) {{
    this.attributes[name] = value;
    this[name] = value;
  }},
  removeAttribute(name) {{
    delete this.attributes[name];
    delete this[name];
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
const requests = [];
const fetchImpl = async (url, options) => {{
  requests.push({{
    url,
    method: options?.method || "GET",
    body: options?.body || "",
  }});
  return {{
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
  }};
}};

await enhanceProfileNav(doc, storage, fetchImpl);
process.stdout.write(JSON.stringify({{
  ariaDisabled: navLink["aria-disabled"] || "",
  tabindex: navLink.tabindex || "",
  state: navLink["data-profile-nav-state"] || "",
  href: navLink.href,
  textContent: navLink.textContent,
  fingerprint,
  requests,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertEqual(payload["ariaDisabled"], "")
        self.assertEqual(payload["tabindex"], "")
        self.assertEqual(payload["state"], "resolved")
        self.assertEqual(payload["href"], f"/profiles/openpgp-{payload['fingerprint']}/merge")
        self.assertEqual(payload["textContent"], "My profile (3)")
        self.assertEqual(payload["requests"][0]["url"], "/api/set_identity_hint")
        self.assertEqual(payload["requests"][0]["method"], "POST")
        self.assertIn("fingerprint", payload["requests"][0]["body"])
        self.assertTrue(payload["requests"][1]["url"].startswith("/api/get_merge_management?identity_id=openpgp%3A"))

    def test_profile_nav_asset_leaves_unresolved_slot_stable_without_stored_key(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_nav.js").as_uri()
        vendor_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        script = f"""
import fs from "node:fs/promises";
const loaderSource = await fs.readFile(new URL({json.dumps((Path(__file__).resolve().parent.parent / "templates" / "assets" / "openpgp_loader.js").as_uri())}), "utf8");
const rewrittenLoaderSource = loaderSource.replace(
  "./vendor/openpgp.min.mjs",
  {json.dumps(vendor_url)},
);
const loaderModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenLoaderSource).toString("base64")}}`;
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewrittenAssetSource = assetSource.replace(
  "./openpgp_loader.js",
  loaderModuleUrl,
);
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenAssetSource).toString("base64")}}`;
const {{ enhanceProfileNav }} = await import(assetModuleUrl);

const navLink = {{
  attributes: {{
    "aria-disabled": "true",
    "data-profile-nav-state": "unresolved",
    "data-merge-feature-enabled": "0",
    tabindex: "-1",
  }},
  textContent: "My profile",
  href: "",
  setAttribute(name, value) {{
    this.attributes[name] = value;
    this[name] = value;
  }},
  removeAttribute(name) {{
    delete this.attributes[name];
    delete this[name];
  }},
}};
const doc = {{
  querySelector(selector) {{
    return selector === "[data-profile-nav-link]" ? navLink : null;
  }},
}};
const storage = {{
  getItem() {{
    return "";
  }},
}};
let fetchCalls = 0;
const fetchImpl = async () => {{
  fetchCalls += 1;
  return {{ ok: true, text: async () => "" }};
}};

await enhanceProfileNav(doc, storage, fetchImpl);
process.stdout.write(JSON.stringify({{
  ariaDisabled: navLink.attributes["aria-disabled"] || "",
  tabindex: navLink.attributes.tabindex || "",
  state: navLink.attributes["data-profile-nav-state"] || "",
  href: navLink.href,
  textContent: navLink.textContent,
  fetchCalls,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertEqual(payload["ariaDisabled"], "true")
        self.assertEqual(payload["tabindex"], "-1")
        self.assertEqual(payload["state"], "unresolved")
        self.assertEqual(payload["href"], "")
        self.assertEqual(payload["textContent"], "My profile")
        self.assertEqual(payload["fetchCalls"], 1)

    def test_profile_nav_asset_skips_merge_notification_fetch_when_feature_disabled(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_nav.js").as_uri()
        vendor_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        script = f"""
import fs from "node:fs/promises";
import * as openpgp from {json.dumps(vendor_url)};
const loaderSource = await fs.readFile(new URL({json.dumps((Path(__file__).resolve().parent.parent / "templates" / "assets" / "openpgp_loader.js").as_uri())}), "utf8");
const rewrittenLoaderSource = loaderSource.replace(
  "./vendor/openpgp.min.mjs",
  {json.dumps(vendor_url)},
);
const loaderModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenLoaderSource).toString("base64")}}`;
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewrittenAssetSource = assetSource.replace(
  "./openpgp_loader.js",
  loaderModuleUrl,
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
let fetchCount = 0;
const navLink = {{
  attributes: {{"data-merge-feature-enabled": "0"}},
  textContent: "My profile",
  setAttribute(name, value) {{
    this.attributes[name] = value;
    this[name] = value;
  }},
  removeAttribute(name) {{
    delete this.attributes[name];
    delete this[name];
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

await enhanceProfileNav(doc, storage, async () => {{
  fetchCount += 1;
  return {{ ok: true, text: async () => "" }};
}});
process.stdout.write(JSON.stringify({{
  href: navLink.href,
  textContent: navLink.textContent,
  fetchCount,
  fingerprint,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertEqual(payload["href"], f"/profiles/openpgp-{payload['fingerprint']}?self=1")
        self.assertEqual(payload["textContent"], "My profile")
        self.assertEqual(payload["fetchCount"], 1)


if __name__ == "__main__":
    unittest.main()
