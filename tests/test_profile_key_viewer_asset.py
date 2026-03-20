from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


class ProfileKeyViewerAssetTests(unittest.TestCase):
    def run_node(self, script: str) -> str:
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", script],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    def test_asset_populates_account_key_page_targets(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_key_viewer.js").as_uri()
        script = f"""
import fs from "node:fs/promises";
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(assetSource).toString("base64")}}`;
const {{ enhanceProfileKeyViewer }} = await import(assetModuleUrl);

const statusNode = {{ textContent: "" }};
const privateNode = {{ value: "" }};
const publicNode = {{ value: "" }};
globalThis.document = {{
  getElementById(id) {{
    if (id === "key-material-status") return statusNode;
    if (id === "key-private-key-output") return privateNode;
    if (id === "key-public-key-output") return publicNode;
    return null;
  }},
}};

enhanceProfileKeyViewer({{
  getItem(key) {{
    if (key === "forum_private_key_armored") return "PRIVATE";
    if (key === "forum_public_key_armored") return "PUBLIC";
    return "";
  }},
}});

process.stdout.write(JSON.stringify({{
  status: statusNode.textContent,
  privateValue: privateNode.value,
  publicValue: publicNode.value,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertEqual(payload["status"], "Showing the browser-stored signing key for this device.")
        self.assertEqual(payload["privateValue"], "PRIVATE")
        self.assertEqual(payload["publicValue"], "PUBLIC")

    def test_asset_falls_back_to_legacy_profile_targets(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_key_viewer.js").as_uri()
        script = f"""
import fs from "node:fs/promises";
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(assetSource).toString("base64")}}`;
const {{ enhanceProfileKeyViewer }} = await import(assetModuleUrl);

const statusNode = {{ textContent: "" }};
const privateNode = {{ value: "" }};
const publicNode = {{ value: "" }};
globalThis.document = {{
  getElementById(id) {{
    if (id === "profile-key-status") return statusNode;
    if (id === "profile-private-key-output") return privateNode;
    if (id === "profile-public-key-output") return publicNode;
    return null;
  }},
}};

enhanceProfileKeyViewer({{
  getItem(key) {{
    if (key === "forum_private_key_armored") return "";
    if (key === "forum_public_key_armored") return "PUBLIC";
    return "";
  }},
}});

process.stdout.write(JSON.stringify({{
  status: statusNode.textContent,
  privateValue: privateNode.value,
  publicValue: publicNode.value,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertEqual(
            payload["status"],
            "A public key is saved in this browser, but the private key is not available here.",
        )
        self.assertEqual(payload["privateValue"], "")
        self.assertEqual(payload["publicValue"], "PUBLIC")


if __name__ == "__main__":
    unittest.main()
