import { ensureLocalKeys } from "./browser_signing.js";
import { enhanceProfileKeyViewer } from "./profile_key_viewer.js";

function $(id) {
  return document.getElementById(id);
}

function setStatus(message) {
  const element = $("key-material-status");
  if (element) {
    element.textContent = message;
  }
}

function setButtonsDisabled(disabled) {
  const generateButton = $("generate-key-button");
  const importButton = $("import-key-button");
  if (generateButton) {
    generateButton.disabled = disabled;
  }
  if (importButton) {
    importButton.disabled = disabled;
  }
}

function requiredTrimmed(value, fieldName) {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error(`${fieldName} is required`);
  }
  return trimmed;
}

async function runKeyAction(action, successMessage) {
  setButtonsDisabled(true);
  try {
    await action();
    await enhanceProfileKeyViewer();
    setStatus(successMessage);
  } catch (error) {
    setStatus(error && error.message ? error.message : String(error));
  } finally {
    setButtonsDisabled(false);
  }
}

export function enhanceAccountKeyActions() {
  const generateButton = $("generate-key-button");
  const importButton = $("import-key-button");
  const privateKeyOutput = $("key-private-key-output");
  if (!generateButton || !importButton || !privateKeyOutput) {
    return;
  }

  generateButton.addEventListener("click", async () => {
    setStatus("Generating a new local signing key...");
    await runKeyAction(
      () => ensureLocalKeys({ forceGenerate: true }),
      "Generated and stored a fresh local signing key.",
    );
  });

  importButton.addEventListener("click", async () => {
    setStatus("Importing the provided private key...");
    await runKeyAction(
      () => ensureLocalKeys({ importedPrivateKey: requiredTrimmed(privateKeyOutput.value, "private key") }),
      "Imported and stored the provided local signing key.",
    );
  });
}

if (typeof document !== "undefined") {
  enhanceAccountKeyActions();
}
