from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


class ProfileMergeSuggestionAssetTests(unittest.TestCase):
    def run_node(self, script: str) -> str:
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", script],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    def test_profile_merge_suggestion_asset_hides_previously_dismissed_suggestion(self) -> None:
        asset_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_merge_suggestion.js"
        ).as_uri()
        script = f"""
import fs from "node:fs/promises";

const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(assetSource).toString("base64")}}`;
const {{ enhanceMergeSuggestion, mergeSuggestionKey }} = await import(assetModuleUrl);

const section = {{
  hidden: false,
  getAttribute(name) {{
    if (name === "data-identity-id") return "openpgp:beta";
    if (name === "data-other-identity-id") return "openpgp:alpha";
    return "";
  }},
  querySelector() {{
    return null;
  }},
}};
const doc = {{
  querySelectorAll(selector) {{
    return selector === "[data-merge-suggestion]" ? [section] : [];
  }},
}};
const storage = {{
  getItem(key) {{
    return key === mergeSuggestionKey("openpgp:beta", "openpgp:alpha") ? "1" : "";
  }},
}};

enhanceMergeSuggestion(doc, storage);
process.stdout.write(JSON.stringify({{ hidden: section.hidden }}));
"""
        payload = json.loads(self.run_node(script))

        self.assertTrue(payload["hidden"])

    def test_profile_merge_suggestion_asset_persists_not_me_dismissal(self) -> None:
        asset_url = (
            Path(__file__).resolve().parent.parent / "templates" / "assets" / "profile_merge_suggestion.js"
        ).as_uri()
        script = f"""
import fs from "node:fs/promises";

const assetSource = await fs.readFile(new URL({json.dumps(asset_url)}), "utf8");
const assetModuleUrl = `data:text/javascript;base64,${{Buffer.from(assetSource).toString("base64")}}`;
const {{ enhanceMergeSuggestion, mergeSuggestionKey }} = await import(assetModuleUrl);

let clickHandler = null;
const dismissButton = {{
  hidden: true,
  addEventListener(name, handler) {{
    if (name === "click") clickHandler = handler;
  }},
}};
const section = {{
  hidden: false,
  getAttribute(name) {{
    if (name === "data-identity-id") return "openpgp:beta";
    if (name === "data-other-identity-id") return "openpgp:alpha";
    return "";
  }},
  querySelector(selector) {{
    return selector === "[data-dismiss-merge-suggestion]" ? dismissButton : null;
  }},
}};
const doc = {{
  querySelectorAll(selector) {{
    return selector === "[data-merge-suggestion]" ? [section] : [];
  }},
}};
const writes = {{}};
const storage = {{
  getItem() {{
    return "";
  }},
  setItem(key, value) {{
    writes[key] = value;
  }},
}};

enhanceMergeSuggestion(doc, storage);
clickHandler();
process.stdout.write(JSON.stringify({{
  buttonHidden: dismissButton.hidden,
  sectionHidden: section.hidden,
  dismissedValue: writes[mergeSuggestionKey("openpgp:beta", "openpgp:alpha")] || "",
}}));
"""
        payload = json.loads(self.run_node(script))

        self.assertFalse(payload["buttonHidden"])
        self.assertTrue(payload["sectionHidden"])
        self.assertEqual(payload["dismissedValue"], "1")


if __name__ == "__main__":
    unittest.main()
