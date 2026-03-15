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

function normalizeNewlines(text) {
  return text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

function ensureAscii(text, fieldName) {
  if (!/^[\x00-\x7F]*$/.test(text)) {
    throw new Error(`${fieldName} must be ASCII`);
  }
}

function requiredTrimmed(value, fieldName) {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error(`${fieldName} is required`);
  }
  return trimmed;
}

function normalizeBoardTags(text) {
  return text.trim().split(/\s+/).filter(Boolean).join(" ");
}

function firstNonEmptyLine(text) {
  for (const line of normalizeNewlines(text).split("\n")) {
    const trimmed = line.trim();
    if (trimmed) {
      return trimmed;
    }
  }
  return "";
}

function deriveSubjectFromBody(bodyText) {
  return firstNonEmptyLine(bodyText).slice(0, 72);
}

function slugFromBody(bodyText) {
  const firstLine = firstNonEmptyLine(bodyText).toLowerCase();
  const slug = firstLine.replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return slug.slice(0, 24) || "note";
}

function timestampToken() {
  return new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
}

function randomToken() {
  const bytes = new Uint8Array(4);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function generatePostId(commandName, bodyText) {
  const prefix = commandName === "create_thread" ? "thread" : "reply";
  return `${prefix}-${timestampToken()}-${slugFromBody(bodyText)}-${randomToken()}`;
}

function loadKeys() {
  return {
    privateKey: localStorage.getItem(STORAGE_PRIVATE) || "",
    publicKey: localStorage.getItem(STORAGE_PUBLIC) || "",
  };
}

function saveKeys(privateKey, publicKey) {
  localStorage.setItem(STORAGE_PRIVATE, privateKey);
  localStorage.setItem(STORAGE_PUBLIC, publicKey);
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

function responseRecordId(responseText) {
  const match = responseText.match(/^Record-ID:\s+(.+)$/m);
  return match ? match[1].trim() : "";
}

function redirectTarget(commandName, recordId) {
  if (!recordId) {
    return "";
  }
  if (commandName === "create_thread") {
    return `/threads/${encodeURIComponent(recordId)}`;
  }
  return `/posts/${encodeURIComponent(recordId)}`;
}

function formState() {
  return {
    body: $("body-input"),
  };
}

function defaultContext(root) {
  return {
    boardTags: normalizeBoardTags(root.dataset.boardTags || "general"),
    threadId: (root.dataset.threadId || "").trim(),
    parentId: (root.dataset.parentId || "").trim(),
  };
}

function buildCanonicalPayload(form, commandName, defaults) {
  const body = normalizeNewlines(requiredTrimmed(form.body.value, "Body")).replace(/\n*$/, "\n");
  const postId = generatePostId(commandName, body);
  const boardTags = requiredTrimmed(defaults.boardTags, "Board-Tags");
  const subject = commandName === "create_thread" ? deriveSubjectFromBody(body) : "";

  ensureAscii(postId, "Post-ID");
  ensureAscii(boardTags, "Board-Tags");
  ensureAscii(subject, "Subject");
  ensureAscii(defaults.threadId, "Thread-ID");
  ensureAscii(defaults.parentId, "Parent-ID");
  ensureAscii(body, "Body");

  const headers = [
    `Post-ID: ${postId}`,
    `Board-Tags: ${boardTags}`,
  ];
  if (subject) {
    headers.push(`Subject: ${subject}`);
  }

  if (commandName === "create_reply") {
    headers.push(`Thread-ID: ${requiredTrimmed(defaults.threadId, "Thread-ID")}`);
    headers.push(`Parent-ID: ${requiredTrimmed(defaults.parentId, "Parent-ID")}`);
  } else if (defaults.threadId || defaults.parentId) {
    throw new Error("Thread-ID and Parent-ID must be blank for a new thread");
  }

  return {
    payload: `${headers.join("\n")}\n\n${body}`,
    postId,
    subject,
  };
}

function updatePayloadPreview(form, commandName, defaults) {
  const payloadOutput = $("payload-output");
  if (!payloadOutput) {
    return;
  }
  try {
    if (!form.body.value.trim()) {
      payloadOutput.value = "";
      return;
    }
    payloadOutput.value = buildCanonicalPayload(form, commandName, defaults).payload;
  } catch (_error) {
    payloadOutput.value = "";
  }
}

async function deriveStoredKeys() {
  const stored = loadKeys();
  if (!stored.privateKey) {
    return null;
  }
  if (stored.publicKey) {
    return stored;
  }
  const publicKey = await privateToPublic(stored.privateKey);
  saveKeys(stored.privateKey, publicKey);
  return {
    privateKey: stored.privateKey,
    publicKey,
  };
}

async function ensureLocalKeys({ forceGenerate = false, importedPrivateKey = "" } = {}) {
  let privateKey = importedPrivateKey;
  let publicKey = "";

  if (importedPrivateKey) {
    ensureAscii(importedPrivateKey, "private key");
    publicKey = await privateToPublic(importedPrivateKey);
  } else if (!forceGenerate) {
    const stored = await deriveStoredKeys();
    if (stored) {
      return stored;
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
  const root = $("compose-app");
  if (!root) {
    return;
  }

  const commandName = root.dataset.command || "create_thread";
  const endpoint = root.dataset.endpoint || "/api/create_thread";
  const dryRun = root.dataset.dryRun === "true";
  const defaults = defaultContext(root);
  const state = formState();
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
      return keys;
    } finally {
      signSubmitButton.disabled = false;
    }
  }

  state.body.addEventListener("input", () => {
    updatePayloadPreview(state, commandName, defaults);
    signatureOutput.value = "";
    responseOutput.value = "";
  });

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
      const privateKey = requiredTrimmed(privateKeyInput.value, "private key");
      const keys = await prepareKeys(
        { importedPrivateKey: privateKey },
        "Imported and stored the provided local signing key.",
      );
      applyKeys(keys);
    } catch (error) {
      setStatus("key-status", `Key import failed: ${error.message}`);
    }
  });

  updatePayloadPreview(state, commandName, defaults);
  setStatus("key-status", "Preparing local signing key...");
  try {
    const keys = await prepareKeys({}, "Local signing key is ready.");
    applyKeys(keys);
  } catch (error) {
    setStatus("key-status", `Key setup failed: ${error.message}`);
  }

  $("signed-post-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    signSubmitButton.disabled = true;
    setStatus("submit-status", "Building canonical payload...");
    responseOutput.value = "";
    signatureOutput.value = "";

    try {
      const keys = currentKeys || await ensureLocalKeys();
      applyKeys(keys);
      const built = buildCanonicalPayload(state, commandName, defaults);
      payloadOutput.value = built.payload;
      setStatus("submit-status", "Signing payload...");
      const signature = await signPayload(built.payload, keys.privateKey);

      signatureOutput.value = signature;
      setStatus("submit-status", dryRun ? "Submitting signed preview..." : "Submitting signed post...");

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          payload: built.payload,
          signature,
          public_key: keys.publicKey,
          dry_run: dryRun,
        }),
      });
      const responseText = await response.text();
      responseOutput.value = responseText;

      if (!response.ok) {
        throw new Error(responseText.trim() || `Request failed with status ${response.status}`);
      }

      const recordId = responseRecordId(responseText);
      if (dryRun) {
        setStatus("submit-status", "Signed preview accepted.");
      } else {
        setStatus("submit-status", "Signed post accepted. Redirecting...");
        const target = redirectTarget(commandName, recordId);
        if (target) {
          window.setTimeout(() => {
            window.location.assign(target);
          }, 500);
        }
      }
    } catch (error) {
      setStatus("submit-status", `Signed posting failed: ${error.message}`);
    } finally {
      signSubmitButton.disabled = false;
    }
  });
}

main();
