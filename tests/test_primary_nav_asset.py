from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


class PrimaryNavAssetTests(unittest.TestCase):
    def run_node(self, script: str) -> str:
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", script],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    def test_handle_primary_nav_activation_marks_clicked_link_pending(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "primary_nav.js").as_uri()
        script = f"""
import fs from "node:fs/promises";
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(assetSource).toString("base64")}}`;
const {{ handlePrimaryNavActivation }} = await import(assetModuleUrl);

const navRoot = {{
  attributes: {{}},
  setAttribute(name, value) {{
    this.attributes[name] = value;
  }},
}};
const link = {{
  attributes: {{
    href: "/activity/",
  }},
  setAttribute(name, value) {{
    this.attributes[name] = value;
  }},
  getAttribute(name) {{
    return this.attributes[name] || "";
  }},
}};
const event = {{
  defaultPrevented: false,
  button: 0,
  metaKey: false,
  ctrlKey: false,
  shiftKey: false,
  altKey: false,
  target: {{
    closest(selector) {{
      return selector === "[data-primary-nav-link]" ? link : null;
    }},
  }},
}};

const handled = handlePrimaryNavActivation(event, navRoot);
process.stdout.write(JSON.stringify({{
  handled,
  navRoot: navRoot.attributes,
  link: link.attributes,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertTrue(payload["handled"])
        self.assertEqual(payload["navRoot"]["data-primary-nav-pending"], "true")
        self.assertEqual(payload["navRoot"]["aria-busy"], "true")
        self.assertEqual(payload["navRoot"]["data-primary-nav-pending-href"], "/activity/")
        self.assertEqual(payload["link"]["data-primary-nav-pending"], "true")

    def test_handle_primary_nav_activation_ignores_modified_clicks(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "primary_nav.js").as_uri()
        script = f"""
import fs from "node:fs/promises";
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(assetSource).toString("base64")}}`;
const {{ handlePrimaryNavActivation }} = await import(assetModuleUrl);

const navRoot = {{
  attributes: {{}},
  setAttribute(name, value) {{
    this.attributes[name] = value;
  }},
}};
const link = {{
  attributes: {{
    href: "/activity/",
  }},
  setAttribute(name, value) {{
    this.attributes[name] = value;
  }},
  getAttribute(name) {{
    return this.attributes[name] || "";
  }},
}};
const event = {{
  defaultPrevented: false,
  button: 0,
  metaKey: true,
  ctrlKey: false,
  shiftKey: false,
  altKey: false,
  target: {{
    closest(selector) {{
      return selector === "[data-primary-nav-link]" ? link : null;
    }},
  }},
}};

const handled = handlePrimaryNavActivation(event, navRoot);
process.stdout.write(JSON.stringify({{
  handled,
  navRoot: navRoot.attributes,
  link: link.attributes,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertFalse(payload["handled"])
        self.assertEqual(payload["navRoot"], {})
        self.assertEqual(payload["link"], {"href": "/activity/"})

    def test_handle_primary_nav_activation_ignores_disabled_profile_slot(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "primary_nav.js").as_uri()
        script = f"""
import fs from "node:fs/promises";
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(assetSource).toString("base64")}}`;
const {{ handlePrimaryNavActivation }} = await import(assetModuleUrl);

const navRoot = {{
  attributes: {{}},
  setAttribute(name, value) {{
    this.attributes[name] = value;
  }},
}};
const link = {{
  attributes: {{
    href: "",
    "aria-disabled": "true",
  }},
  setAttribute(name, value) {{
    this.attributes[name] = value;
  }},
  getAttribute(name) {{
    return this.attributes[name] || "";
  }},
}};
const event = {{
  defaultPrevented: false,
  button: 0,
  metaKey: false,
  ctrlKey: false,
  shiftKey: false,
  altKey: false,
  target: {{
    closest(selector) {{
      return selector === "[data-primary-nav-link]" ? link : null;
    }},
  }},
}};

const handled = handlePrimaryNavActivation(event, navRoot);
process.stdout.write(JSON.stringify({{
  handled,
  navRoot: navRoot.attributes,
  link: link.attributes,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertFalse(payload["handled"])
        self.assertEqual(payload["navRoot"], {})
        self.assertEqual(payload["link"], {"href": "", "aria-disabled": "true"})

    def test_enhance_primary_nav_registers_click_handler_on_shared_nav(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "primary_nav.js").as_uri()
        script = f"""
import fs from "node:fs/promises";
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(assetSource).toString("base64")}}`;
const {{ enhancePrimaryNav }} = await import(assetModuleUrl);

const registered = [];
const navRoot = {{
  addEventListener(type, handler, options) {{
    registered.push({{
      type,
      hasHandler: typeof handler === "function",
      useCapture: options === true,
    }});
  }},
}};
const doc = {{
  querySelector(selector) {{
    return selector === "[data-primary-nav]" ? navRoot : null;
  }},
}};

const enhanced = enhancePrimaryNav(doc);
process.stdout.write(JSON.stringify({{
  enhanced,
  registered,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertTrue(payload["enhanced"])
        self.assertEqual(
            payload["registered"],
            [
                {"type": "click", "hasHandler": True, "useCapture": False},
                {"type": "pointerenter", "hasHandler": True, "useCapture": True},
                {"type": "focusin", "hasHandler": True, "useCapture": False},
            ],
        )

    def test_prefetch_primary_nav_href_only_prefetches_allowlisted_destinations(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "primary_nav.js").as_uri()
        script = f"""
import fs from "node:fs/promises";
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(assetSource).toString("base64")}}`;
const {{ prefetchPrimaryNavHref }} = await import(assetModuleUrl);

const appended = [];
const prefetched = new Set();
const doc = {{
  head: {{
    appendChild(node) {{
      appended.push(node.attributes);
      prefetched.add(node.attributes.href);
    }},
  }},
  querySelector(selector) {{
    const match = selector.match(/href="([^"]+)"/);
    if (!match) {{
      return null;
    }}
    return prefetched.has(match[1]) ? {{}} : null;
  }},
  createElement() {{
    return {{
      attributes: {{}},
      setAttribute(name, value) {{
        this.attributes[name] = value;
      }},
    }};
  }},
}};

const firstAllowed = prefetchPrimaryNavHref("/activity/", doc);
const duplicateAllowed = prefetchPrimaryNavHref("/activity/", doc);
const disallowed = prefetchPrimaryNavHref("/profiles/openpgp-test?self=1", doc);
process.stdout.write(JSON.stringify({{
  firstAllowed,
  duplicateAllowed,
  disallowed,
  appended,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertTrue(payload["firstAllowed"])
        self.assertFalse(payload["duplicateAllowed"])
        self.assertFalse(payload["disallowed"])
        self.assertEqual(
            payload["appended"],
            [{"rel": "prefetch", "href": "/activity/", "as": "document"}],
        )

    def test_primary_nav_pending_contract_coexists_with_resolved_profile_nav(self) -> None:
        primary_asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "primary_nav.js").as_uri()
        profile_asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_nav.js").as_uri()
        vendor_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "vendor" / "openpgp.min.mjs"
        ).as_uri()
        loader_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "openpgp_loader.js"
        ).as_uri()
        script = f"""
import fs from "node:fs/promises";
import * as openpgp from {json.dumps(vendor_url)};

const primaryAssetSource = await fs.readFile(new URL({json.dumps(primary_asset_url)}), "utf8");
const primaryAssetModuleUrl = `data:text/javascript;base64,${{Buffer.from(primaryAssetSource).toString("base64")}}`;
const loaderSource = await fs.readFile(new URL({json.dumps(loader_url)}), "utf8");
const rewrittenLoaderSource = loaderSource.replace(
  "./vendor/openpgp.min.mjs",
  {json.dumps(vendor_url)},
);
const loaderModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenLoaderSource).toString("base64")}}`;
const profileAssetSource = await fs.readFile(new URL({json.dumps(profile_asset_url)}), "utf8");
const rewrittenProfileAssetSource = profileAssetSource.replace(
  "./openpgp_loader.js",
  loaderModuleUrl,
);
const profileAssetModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewrittenProfileAssetSource).toString("base64")}}`;
const {{ handlePrimaryNavActivation }} = await import(primaryAssetModuleUrl);
const {{ enhanceProfileNav }} = await import(profileAssetModuleUrl);

const generated = await openpgp.generateKey({{
  type: "ecc",
  curve: "ed25519",
  userIDs: [{{ name: "Primary Nav Profile Test" }}],
  format: "armored",
}});
const publicKey = await openpgp.readKey({{ armoredKey: generated.publicKey }});
const fingerprint = publicKey.getFingerprint().toLowerCase();
const navRoot = {{
  attributes: {{}},
  setAttribute(name, value) {{
    this.attributes[name] = value;
  }},
}};
const navLink = {{
  attributes: {{
    "data-merge-feature-enabled": "0",
    "data-profile-nav-state": "unresolved",
  }},
  textContent: "My profile",
  setAttribute(name, value) {{
    this.attributes[name] = value;
    this[name] = value;
  }},
  removeAttribute(name) {{
    delete this.attributes[name];
    delete this[name];
  }},
  getAttribute(name) {{
    return this.attributes[name] || "";
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
const fetchImpl = async () => {{
  return {{
    ok: true,
    async text() {{
      return "";
    }},
  }};
}};

await enhanceProfileNav(doc, storage, fetchImpl);
const handled = handlePrimaryNavActivation({{
  defaultPrevented: false,
  button: 0,
  metaKey: false,
  ctrlKey: false,
  shiftKey: false,
  altKey: false,
  target: {{
    closest(selector) {{
      return selector === "[data-primary-nav-link]" ? navLink : null;
    }},
  }},
}}, navRoot);
process.stdout.write(JSON.stringify({{
  handled,
  href: navLink.href,
  navRoot: navRoot.attributes,
  navLink: navLink.attributes,
  fingerprint,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertTrue(payload["handled"])
        self.assertEqual(payload["href"], f"/profiles/openpgp-{payload['fingerprint']}?self=1")
        self.assertEqual(payload["navRoot"]["data-primary-nav-pending"], "true")
        self.assertEqual(payload["navLink"]["data-primary-nav-pending"], "true")


if __name__ == "__main__":
    unittest.main()
