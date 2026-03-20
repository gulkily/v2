from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


class AccountKeyActionsAssetTests(unittest.TestCase):
    def run_node(self, script: str) -> str:
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", script],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    def test_generate_button_uses_force_generate_and_updates_status(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "account_key_actions.js").as_uri()
        script = f"""
import fs from "node:fs/promises";
const browserSigningStub = `export async function ensureLocalKeys(options = {{}}) {{
  globalThis.__ensureCalls.push(options);
  return {{ privateKey: "PRIVATE", publicKey: "PUBLIC" }};
}}`;
const profileViewerStub = `export async function enhanceProfileKeyViewer() {{
  globalThis.__viewerCalls += 1;
}}`;
globalThis.__ensureCalls = [];
globalThis.__viewerCalls = 0;
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewritten = assetSource
  .replace("./browser_signing.js", `data:text/javascript;base64,${{Buffer.from(browserSigningStub).toString("base64")}}`)
  .replace("./profile_key_viewer.js", `data:text/javascript;base64,${{Buffer.from(profileViewerStub).toString("base64")}}`);
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewritten).toString("base64")}}`;

function createButton() {{
  return {{
    disabled: false,
    listeners: {{}},
    addEventListener(name, handler) {{
      this.listeners[name] = handler;
    }},
  }};
}}

const statusNode = {{ textContent: "" }};
const privateNode = {{ value: "" }};
const generateButton = createButton();
const importButton = createButton();
globalThis.document = {{
  getElementById(id) {{
    if (id === "key-material-status") return statusNode;
    if (id === "key-private-key-output") return privateNode;
    if (id === "generate-key-button") return generateButton;
    if (id === "import-key-button") return importButton;
    return null;
  }},
}};

const {{ enhanceAccountKeyActions }} = await import(assetModuleUrl);
enhanceAccountKeyActions();
await generateButton.listeners.click();

process.stdout.write(JSON.stringify({{
  status: statusNode.textContent,
  ensureCalls: globalThis.__ensureCalls,
  viewerCalls: globalThis.__viewerCalls,
  generateDisabled: generateButton.disabled,
  importDisabled: importButton.disabled,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertEqual(payload["status"], "Generated and stored a fresh local signing key.")
        self.assertEqual(payload["ensureCalls"], [{"forceGenerate": True}])
        self.assertEqual(payload["viewerCalls"], 1)
        self.assertFalse(payload["generateDisabled"])
        self.assertFalse(payload["importDisabled"])

    def test_import_button_uses_private_key_textarea_value(self) -> None:
        asset_url = (Path(__file__).resolve().parent.parent / "templates" / "assets" / "account_key_actions.js").as_uri()
        script = f"""
import fs from "node:fs/promises";
const browserSigningStub = `export async function ensureLocalKeys(options = {{}}) {{
  globalThis.__ensureCalls.push(options);
  return {{ privateKey: options.importedPrivateKey, publicKey: "PUBLIC" }};
}}`;
const profileViewerStub = `export async function enhanceProfileKeyViewer() {{
  globalThis.__viewerCalls += 1;
}}`;
globalThis.__ensureCalls = [];
globalThis.__viewerCalls = 0;
const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const rewritten = assetSource
  .replace("./browser_signing.js", `data:text/javascript;base64,${{Buffer.from(browserSigningStub).toString("base64")}}`)
  .replace("./profile_key_viewer.js", `data:text/javascript;base64,${{Buffer.from(profileViewerStub).toString("base64")}}`);
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(rewritten).toString("base64")}}`;

function createButton() {{
  return {{
    disabled: false,
    listeners: {{}},
    addEventListener(name, handler) {{
      this.listeners[name] = handler;
    }},
  }};
}}

const statusNode = {{ textContent: "" }};
const privateNode = {{ value: "  PRIVATE KEY  " }};
const generateButton = createButton();
const importButton = createButton();
globalThis.document = {{
  getElementById(id) {{
    if (id === "key-material-status") return statusNode;
    if (id === "key-private-key-output") return privateNode;
    if (id === "generate-key-button") return generateButton;
    if (id === "import-key-button") return importButton;
    return null;
  }},
}};

const {{ enhanceAccountKeyActions }} = await import(assetModuleUrl);
enhanceAccountKeyActions();
await importButton.listeners.click();

process.stdout.write(JSON.stringify({{
  status: statusNode.textContent,
  ensureCalls: globalThis.__ensureCalls,
  viewerCalls: globalThis.__viewerCalls,
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertEqual(payload["status"], "Imported and stored the provided local signing key.")
        self.assertEqual(payload["ensureCalls"], [{"importedPrivateKey": "PRIVATE KEY"}])
        self.assertEqual(payload["viewerCalls"], 1)


if __name__ == "__main__":
    unittest.main()
