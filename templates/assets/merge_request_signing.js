import * as openpgp from "./vendor/openpgp.min.mjs";

const STORAGE_PRIVATE = "forum_private_key_armored";
const STORAGE_PUBLIC = "forum_public_key_armored";

function $(id) {
  return document.getElementById(id);
}

function setStatus(id, message) {
  const element = $(id);
  if (element) {
    element.textContent = message;
  }
}

function requiredTrimmed(value, fieldName) {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error(`${fieldName} is required`);
  }
  return trimmed;
}

function ensureAscii(text, fieldName) {
  if (!/^[\x00-\x7F]*$/.test(text)) {
    throw new Error(`${fieldName} must be ASCII`);
  }
}

function timestampToken() {
  return new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
}

function randomToken() {
  const bytes = new Uint8Array(4);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function isoTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function saveKeys(privateKey, publicKey) {
  localStorage.setItem(STORAGE_PRIVATE, privateKey);
  localStorage.setItem(STORAGE_PUBLIC, publicKey);
}

function loadKeys() {
  return {
    privateKey: localStorage.getItem(STORAGE_PRIVATE) || "",
    publicKey: localStorage.getItem(STORAGE_PUBLIC) || "",
  };
}

async function privateToPublic(armoredPrivateKey) {
  const privateKey = await openpgp.readPrivateKey({ armoredKey: armoredPrivateKey });
  return privateKey.toPublic().armor();
}

async function signPayload(payloadText, armoredPrivateKey) {
  const privateKey = await openpgp.readPrivateKey({ armoredKey: armoredPrivateKey });
  const message = await openpgp.createMessage({ text: payloadText });
  return openpgp.sign({
    message,
    signingKeys: privateKey,
    detached: true,
    format: "armored",
  });
}

async function generateKeypair() {
  const generated = await openpgp.generateKey({
    type: "ecc",
    curve: "ed25519",
    userIDs: [{ name: "forum-user" }],
    format: "armored",
  });
  return {
    privateKey: generated.privateKey,
    publicKey: generated.publicKey,
  };
}

async function identityIdFromPublicKey(armoredPublicKey) {
  const publicKey = await openpgp.readKey({ armoredKey: armoredPublicKey });
  return `openpgp:${publicKey.getFingerprint().toLowerCase()}`;
}

function generateMergeRequestId(actionName) {
  return `merge-request-${actionName.replace(/[^a-z_]+/g, "-")}-${timestampToken()}-${randomToken()}`;
}

async function buildCanonicalPayload(root, publicKey) {
  const action = requiredTrimmed(root.dataset.action || "", "Action");
  const requesterIdentityId = requiredTrimmed(root.dataset.requesterIdentityId || "", "Requester-Identity-ID");
  const targetIdentityId = requiredTrimmed(root.dataset.targetIdentityId || "", "Target-Identity-ID");
  const actorIdentityId = await identityIdFromPublicKey(publicKey);
  const recordId = generateMergeRequestId(action);
  const timestamp = isoTimestamp();

  for (const [value, fieldName] of [
    [action, "Action"],
    [requesterIdentityId, "Requester-Identity-ID"],
    [targetIdentityId, "Target-Identity-ID"],
    [actorIdentityId, "Actor-Identity-ID"],
    [recordId, "Record-ID"],
    [timestamp, "Timestamp"],
  ]) {
    ensureAscii(value, fieldName);
  }

  return [
    `Record-ID: ${recordId}`,
    `Action: ${action}`,
    `Requester-Identity-ID: ${requesterIdentityId}`,
    `Target-Identity-ID: ${targetIdentityId}`,
    `Actor-Identity-ID: ${actorIdentityId}`,
    `Timestamp: ${timestamp}`,
    "",
    "",
  ].join("\n");
}

async function ensureLocalKeys({ forceGenerate = false, importedPrivateKey = "" } = {}) {
  let privateKey = importedPrivateKey;
  let publicKey = "";

  if (importedPrivateKey) {
    ensureAscii(importedPrivateKey, "private key");
    publicKey = await privateToPublic(importedPrivateKey);
  } else if (!forceGenerate) {
    const stored = loadKeys();
    if (stored.privateKey && stored.publicKey) {
      return stored;
    }
    if (stored.privateKey) {
      publicKey = await privateToPublic(stored.privateKey);
      saveKeys(stored.privateKey, publicKey);
      return { privateKey: stored.privateKey, publicKey };
    }
  }

  if (!privateKey) {
    const generated = await generateKeypair();
    privateKey = generated.privateKey;
    publicKey = generated.publicKey;
  }

  saveKeys(privateKey, publicKey);
  return { privateKey, publicKey };
}

async function main() {
  const root = $("merge-request-app");
  if (!root) {
    return;
  }

  const form = $("merge-request-form");
  const privateKeyInput = $("private-key-input");
  const publicKeyOutput = $("public-key-output");
  const payloadOutput = $("payload-output");
  const signatureOutput = $("signature-output");
  const responseOutput = $("response-output");
  const signSubmitButton = $("sign-submit-button");

  let currentKeys = null;

  function applyKeys(keys) {
    currentKeys = keys;
    privateKeyInput.value = keys.privateKey;
    publicKeyOutput.value = keys.publicKey;
  }

  async function prepareKeys(options, successMessage) {
    signSubmitButton.disabled = true;
    try {
      const keys = await ensureLocalKeys(options);
      applyKeys(keys);
      setStatus("key-status", successMessage);
    } finally {
      signSubmitButton.disabled = false;
    }
  }

  $("generate-key-button").addEventListener("click", async () => {
    setStatus("key-status", "Generating a new local signing key...");
    try {
      await prepareKeys({ forceGenerate: true }, "Generated and stored a fresh local signing key.");
    } catch (error) {
      setStatus("key-status", `Key generation failed: ${error.message}`);
    }
  });

  $("import-key-button").addEventListener("click", async () => {
    setStatus("key-status", "Importing the provided private key...");
    try {
      const keys = await ensureLocalKeys({
        importedPrivateKey: requiredTrimmed(privateKeyInput.value, "private key"),
      });
      applyKeys(keys);
      setStatus("key-status", "Imported and stored the provided local signing key.");
    } catch (error) {
      setStatus("key-status", `Key import failed: ${error.message}`);
    }
  });

  setStatus(
    "key-status",
    "Load or import the key you want to use for this merge action. The server will verify whether it is allowed.",
  );

  try {
    const stored = await ensureLocalKeys();
    applyKeys(stored);
    setStatus("key-status", "Loaded the stored local signing key.");
  } catch (_error) {
    // Leave the instructional status in place.
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    signSubmitButton.disabled = true;
    setStatus("submit-status", "Building canonical payload...");
    responseOutput.value = "";
    signatureOutput.value = "";

    try {
      const keys = currentKeys || await ensureLocalKeys();
      applyKeys(keys);
      const payload = await buildCanonicalPayload(root, keys.publicKey);
      payloadOutput.value = payload;

      setStatus("submit-status", "Signing payload...");
      const signature = await signPayload(payload, keys.privateKey);
      signatureOutput.value = signature;

      setStatus("submit-status", "Submitting signed merge action...");
      const response = await fetch("/api/merge_request", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          payload,
          signature,
          public_key: keys.publicKey,
          dry_run: false,
        }),
      });

      const responseText = await response.text();
      responseOutput.value = responseText;
      if (!response.ok) {
        throw new Error(responseText.trim() || `Server returned ${response.status}`);
      }

      setStatus("submit-status", "Signed merge action accepted. Redirecting...");
      const redirectPath = root.dataset.redirectPath || "";
      if (redirectPath) {
        window.setTimeout(() => {
          window.location.href = redirectPath;
        }, 300);
      }
    } catch (error) {
      setStatus("submit-status", `Signed merge action failed: ${error.message}`);
    } finally {
      signSubmitButton.disabled = false;
    }
  });
}

main();
