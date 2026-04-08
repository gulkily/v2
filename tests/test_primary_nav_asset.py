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


if __name__ == "__main__":
    unittest.main()
