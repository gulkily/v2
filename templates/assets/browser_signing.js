import * as openpgp from "./vendor/openpgp.min.mjs";

const STORAGE_PRIVATE = "forum_private_key_armored";
const STORAGE_PUBLIC = "forum_public_key_armored";
const STORAGE_DRAFT_PREFIX = "forum_compose_draft_v1:";
const DRAFT_SAVE_DELAY_MS = 400;

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

function normalizeSingleLineAscii(value, fieldName) {
  const trimmed = requiredTrimmed(value, fieldName);
  if (trimmed.includes("\n") || trimmed.includes("\r")) {
    throw new Error(`${fieldName} must be a single line`);
  }
  ensureAscii(trimmed, fieldName);
  return trimmed;
}

function normalizeRating(value, fieldName) {
  const trimmed = requiredTrimmed(value, fieldName);
  const number = Number.parseFloat(trimmed);
  if (Number.isNaN(number) || number < 0 || number > 1) {
    throw new Error(`${fieldName} must be a decimal rating between 0 and 1`);
  }
  return number.toFixed(2);
}

function normalizeSpaceSeparatedList(text) {
  return text.trim().split(/\s+/).filter(Boolean).join(" ");
}

function normalizeSemicolonList(text) {
  return text
    .split(";")
    .map((part) => part.trim())
    .filter(Boolean)
    .join("; ");
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

function slugFromText(text) {
  const firstLine = firstNonEmptyLine(text).toLowerCase();
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
  return `${prefix}-${timestampToken()}-${slugFromText(bodyText)}-${randomToken()}`;
}

function generateProfileUpdateId(displayName) {
  return `profile-update-${timestampToken()}-${slugFromText(displayName)}-${randomToken()}`;
}

function isoTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
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

function draftStorageAvailable() {
  try {
    const probeKey = `${STORAGE_DRAFT_PREFIX}probe`;
    localStorage.setItem(probeKey, "1");
    localStorage.removeItem(probeKey);
    return true;
  } catch (_error) {
    return false;
  }
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

function redirectTarget(commandName, recordId, defaults) {
  if (commandName === "update_profile") {
    if (!defaults.profileSlug) {
      return "";
    }
    return `/profiles/${encodeURIComponent(defaults.profileSlug)}`;
  }
  if (!recordId) {
    return "";
  }
  if (commandName === "create_thread") {
    return `/threads/${encodeURIComponent(recordId)}`;
  }
  return `/posts/${encodeURIComponent(recordId)}`;
}

function formState(commandName) {
  if (commandName === "update_profile") {
    return {
      displayName: $("display-name-input"),
    };
  }
  return {
    body: $("body-input"),
    taskStatus: $("task-status-input"),
    taskImpact: $("task-impact-input"),
    taskDifficulty: $("task-difficulty-input"),
    taskDependencies: $("task-dependencies-input"),
    taskSources: $("task-sources-input"),
  };
}

function composeDraftContext(commandName, defaults) {
  if (commandName === "update_profile") {
    return null;
  }
  const scopeParts = [
    commandName,
    defaults.threadType || "plain",
    defaults.boardTags || "general",
  ];
  if (commandName === "create_reply") {
    scopeParts.push(defaults.threadId || "");
    scopeParts.push(defaults.parentId || "");
  }
  return {
    storageKey: `${STORAGE_DRAFT_PREFIX}${scopeParts.join("|")}`,
    fields: [
      ["body", "body"],
      ["taskStatus", "taskStatus"],
      ["taskImpact", "taskImpact"],
      ["taskDifficulty", "taskDifficulty"],
      ["taskDependencies", "taskDependencies"],
      ["taskSources", "taskSources"],
    ],
  };
}

function defaultContext(root) {
  const rawDifficulty = Number.parseInt(root.dataset.powDifficulty || "0", 10);
  return {
    boardTags: normalizeBoardTags(root.dataset.boardTags || "general"),
    threadId: (root.dataset.threadId || "").trim(),
    parentId: (root.dataset.parentId || "").trim(),
    threadType: (root.dataset.threadType || "").trim(),
    sourceIdentityId: (root.dataset.sourceIdentityId || "").trim(),
    profileSlug: (root.dataset.profileSlug || "").trim(),
    powEnabled: root.dataset.powEnabled === "true",
    powDifficulty: Number.isFinite(rawDifficulty) && rawDifficulty > 0 ? rawDifficulty : 0,
  };
}

async function fingerprintFromPublicKey(armoredPublicKey) {
  const publicKey = await openpgp.readKey({ armoredKey: armoredPublicKey });
  return publicKey.getFingerprint().toUpperCase();
}

function buildPowMessage({ fingerprint, postId, difficulty, nonce }) {
  return `forum-pow-v1\n${fingerprint}\n${postId}\n${difficulty}\n${nonce.toLowerCase()}\n`;
}

function countLeadingZeroBits(bytes) {
  let count = 0;
  for (const byte of bytes) {
    if (byte === 0) {
      count += 8;
      continue;
    }
    for (let shift = 7; shift >= 0; shift -= 1) {
      if ((byte & (1 << shift)) === 0) {
        count += 1;
      } else {
        return count;
      }
    }
  }
  return count;
}

async function sha256Bytes(text) {
  const encoded = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", encoded);
  return new Uint8Array(digest);
}

async function solveProofOfWork({ fingerprint, postId, difficulty, onProgress }) {
  let nonce = 0;
  while (true) {
    const candidate = nonce.toString(16);
    const digest = await sha256Bytes(
      buildPowMessage({
        fingerprint,
        postId,
        difficulty,
        nonce: candidate,
      }),
    );
    if (countLeadingZeroBits(digest) >= difficulty) {
      return `v1:${candidate}`;
    }
    nonce += 1;
    if (nonce % 250 === 0) {
      if (onProgress) {
        onProgress(nonce);
      }
      await new Promise((resolve) => window.setTimeout(resolve, 0));
    }
  }
}

function normalizeDisplayName(displayName) {
  const value = requiredTrimmed(displayName, "Display-Name");
  if (value.includes("\n") || value.includes("\r")) {
    throw new Error("Display-Name must be a single line");
  }
  ensureAscii(value, "Display-Name");
  if (value.length > 80) {
    throw new Error("Display-Name must be at most 80 characters");
  }
  return value;
}

function buildCanonicalPostPayload(form, commandName, defaults) {
  const body = normalizeNewlines(requiredTrimmed(form.body.value, "Body")).replace(/\n*$/, "\n");
  const postId = generatePostId(commandName, body);
  const boardTags = requiredTrimmed(defaults.boardTags, "Board-Tags");
  const subject = commandName === "create_thread" ? deriveSubjectFromBody(body) : "";
  const threadType = defaults.threadType ? normalizeSingleLineAscii(defaults.threadType, "Thread-Type") : "";

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
  if (threadType) {
    headers.push(`Thread-Type: ${threadType}`);
    if (threadType === "task") {
      const taskStatus = normalizeSingleLineAscii(form.taskStatus?.value || "", "Task-Status");
      const taskImpact = normalizeRating(form.taskImpact?.value || "", "Task-Presentability-Impact");
      const taskDifficulty = normalizeRating(form.taskDifficulty?.value || "", "Task-Implementation-Difficulty");
      const taskDependencies = normalizeSpaceSeparatedList(form.taskDependencies?.value || "");
      const taskSources = normalizeSemicolonList(form.taskSources?.value || "");

      headers.push(`Task-Status: ${taskStatus}`);
      headers.push(`Task-Presentability-Impact: ${taskImpact}`);
      headers.push(`Task-Implementation-Difficulty: ${taskDifficulty}`);
      if (taskDependencies) {
        ensureAscii(taskDependencies, "Task-Depends-On");
        headers.push(`Task-Depends-On: ${taskDependencies}`);
      }
      if (taskSources) {
        ensureAscii(taskSources, "Task-Sources");
        headers.push(`Task-Sources: ${taskSources}`);
      }
    }
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

function buildCanonicalProfileUpdatePayload(form, defaults) {
  const displayName = normalizeDisplayName(form.displayName.value);
  const recordId = generateProfileUpdateId(displayName);
  const timestamp = isoTimestamp();
  const sourceIdentityId = requiredTrimmed(defaults.sourceIdentityId, "Source-Identity-ID");

  ensureAscii(recordId, "Record-ID");
  ensureAscii(timestamp, "Timestamp");
  ensureAscii(sourceIdentityId, "Source-Identity-ID");

  return {
    payload: [
      `Record-ID: ${recordId}`,
      "Action: set_display_name",
      `Source-Identity-ID: ${sourceIdentityId}`,
      `Timestamp: ${timestamp}`,
      "",
      displayName,
      "",
    ].join("\n"),
    recordId,
    displayName,
  };
}

function buildCanonicalPayload(form, commandName, defaults) {
  if (commandName === "update_profile") {
    return buildCanonicalProfileUpdatePayload(form, defaults);
  }
  return buildCanonicalPostPayload(form, commandName, defaults);
}

function hasPreviewInput(form, commandName) {
  if (commandName === "update_profile") {
    return Boolean(form.displayName.value.trim());
  }
  return Boolean(form.body.value.trim());
}

function formatSavedAt(timestamp) {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleString();
}

function setDraftStatus(message) {
  setStatus("draft-status", message);
}

function loadDraft(storageKey) {
  try {
    const rawValue = localStorage.getItem(storageKey);
    if (!rawValue) {
      return null;
    }
    const parsed = JSON.parse(rawValue);
    if (!parsed || typeof parsed !== "object" || typeof parsed.savedAt !== "string" || !parsed.fields || typeof parsed.fields !== "object") {
      return null;
    }
    return parsed;
  } catch (_error) {
    return null;
  }
}

function saveDraft(storageKey, fields) {
  const draft = {
    savedAt: new Date().toISOString(),
    fields,
  };
  localStorage.setItem(storageKey, JSON.stringify(draft));
  return draft;
}

function clearDraft(storageKey) {
  localStorage.removeItem(storageKey);
}

function applyDraft(state, draftContext, draft) {
  for (const [fieldName, storageName] of draftContext.fields) {
    const input = state[fieldName];
    const value = draft.fields[storageName];
    if (input && typeof value === "string") {
      input.value = value;
    }
  }
}

function captureDraftFields(state, draftContext) {
  const fields = {};
  for (const [fieldName, storageName] of draftContext.fields) {
    const input = state[fieldName];
    if (input) {
      fields[storageName] = input.value;
    }
  }
  return fields;
}

function hasDraftContent(fields) {
  return Object.values(fields).some((value) => typeof value === "string" && value.trim() !== "");
}

function updatePayloadPreview(form, commandName, defaults) {
  const payloadOutput = $("payload-output");
  if (!payloadOutput) {
    return;
  }
  try {
    if (!hasPreviewInput(form, commandName)) {
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
  const root = $("compose-app") || $("profile-update-app");
  if (!root) {
    return;
  }

  const commandName = root.dataset.command || "create_thread";
  const endpoint = root.dataset.endpoint || "/api/create_thread";
  const dryRun = root.dataset.dryRun === "true";
  const defaults = defaultContext(root);
  const state = formState(commandName);
  const form = commandName === "update_profile" ? $("profile-update-form") : $("signed-post-form");
  const privateKeyInput = $("private-key-input");
  const publicKeyOutput = $("public-key-output");
  const payloadOutput = $("payload-output");
  const signatureOutput = $("signature-output");
  const responseOutput = $("response-output");
  const signSubmitButton = $("sign-submit-button");
  const draftContext = composeDraftContext(commandName, defaults);
  const canStoreDraft = Boolean(draftContext) && draftStorageAvailable();
  let currentKeys = null;
  let pendingDraftTimer = 0;

  if (!form || !privateKeyInput || !publicKeyOutput || !payloadOutput || !signatureOutput || !responseOutput || !signSubmitButton) {
    return;
  }

  if (draftContext) {
    if (!canStoreDraft) {
      setDraftStatus("Local draft saving is unavailable in this browser. Compose will still work.");
    } else {
      const savedDraft = loadDraft(draftContext.storageKey);
      if (savedDraft) {
        applyDraft(state, draftContext, savedDraft);
        const restoredAt = formatSavedAt(savedDraft.savedAt);
        setDraftStatus(
          restoredAt
            ? `Restored local draft saved at ${restoredAt}.`
            : "Restored a local draft from this browser.",
        );
      } else {
        setDraftStatus("Drafts are saved locally in this browser.");
      }
    }
  }

  function scheduleDraftSave() {
    if (!draftContext || !canStoreDraft) {
      return;
    }
    window.clearTimeout(pendingDraftTimer);
    pendingDraftTimer = window.setTimeout(() => {
      try {
        const fields = captureDraftFields(state, draftContext);
        if (!hasDraftContent(fields)) {
          clearDraft(draftContext.storageKey);
          setDraftStatus("Drafts are saved locally in this browser.");
          return;
        }
        const savedDraft = saveDraft(draftContext.storageKey, fields);
        const savedAt = formatSavedAt(savedDraft.savedAt);
        setDraftStatus(
          savedAt
            ? `Draft saved locally at ${savedAt}.`
            : "Draft saved locally in this browser.",
        );
      } catch (_error) {
        setDraftStatus("Local draft saving is unavailable in this browser. Compose will still work.");
      }
    }, DRAFT_SAVE_DELAY_MS);
  }

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

  async function prepareInitialKeys() {
    if (commandName === "update_profile") {
      const stored = await deriveStoredKeys();
      if (!stored) {
        setStatus(
          "key-status",
          "Import the private key for this profile, or generate a new one only if it matches this identity.",
        );
        return null;
      }
      applyKeys(stored);
      setStatus("key-status", "Loaded the stored local signing key.");
      return stored;
    }
    return prepareKeys({}, "Local signing key is ready.");
  }

  async function resolveSubmitKeys() {
    if (currentKeys) {
      return currentKeys;
    }
    if (commandName === "update_profile") {
      const stored = await deriveStoredKeys();
      if (stored) {
        applyKeys(stored);
        return stored;
      }
      throw new Error("Load or import the private key for this profile before signing.");
    }
    const keys = await ensureLocalKeys();
    applyKeys(keys);
    return keys;
  }

  function submittingMessage() {
    if (dryRun) {
      return "Submitting signed preview...";
    }
    if (commandName === "update_profile") {
      return "Submitting signed profile update...";
    }
    return "Submitting signed post...";
  }

  function failurePrefix() {
    return commandName === "update_profile" ? "Signed profile update failed" : "Signed posting failed";
  }

  function successMessage() {
    if (dryRun) {
      return "Signed preview accepted.";
    }
    if (commandName === "update_profile") {
      return "Signed profile update accepted. Redirecting...";
    }
    return "Signed post accepted. Redirecting...";
  }

  const previewInputs = commandName === "update_profile"
    ? [state.displayName]
    : [
        state.body,
        state.taskStatus,
        state.taskImpact,
        state.taskDifficulty,
        state.taskDependencies,
        state.taskSources,
      ].filter(Boolean);
  for (const input of previewInputs) {
    input.addEventListener("input", () => {
      updatePayloadPreview(state, commandName, defaults);
      signatureOutput.value = "";
      responseOutput.value = "";
      scheduleDraftSave();
    });
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
    await prepareInitialKeys();
  } catch (error) {
    setStatus("key-status", `Key setup failed: ${error.message}`);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    signSubmitButton.disabled = true;
    setStatus("submit-status", "Building canonical payload...");
    responseOutput.value = "";
    signatureOutput.value = "";

    try {
      const keys = await resolveSubmitKeys();
      const built = buildCanonicalPayload(state, commandName, defaults);
      payloadOutput.value = built.payload;
      setStatus("submit-status", "Signing payload...");
      const signature = await signPayload(built.payload, keys.privateKey);
      let powStamp = null;

      if (defaults.powEnabled && commandName !== "update_profile") {
        const fingerprint = await fingerprintFromPublicKey(keys.publicKey);
        setStatus("submit-status", `Computing proof-of-work (${defaults.powDifficulty} leading zero bits)...`);
        powStamp = await solveProofOfWork({
          fingerprint,
          postId: built.postId,
          difficulty: defaults.powDifficulty,
          onProgress: (attempts) => {
            setStatus(
              "submit-status",
              `Computing proof-of-work (${defaults.powDifficulty} leading zero bits, ${attempts} attempts)...`,
            );
          },
        });
      }

      signatureOutput.value = signature;
      setStatus("submit-status", submittingMessage());

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          payload: built.payload,
          signature,
          public_key: keys.publicKey,
          pow_stamp: powStamp,
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
        setStatus("submit-status", successMessage());
      } else {
        if (draftContext && canStoreDraft) {
          window.clearTimeout(pendingDraftTimer);
          clearDraft(draftContext.storageKey);
          setDraftStatus("Local draft cleared after successful submission.");
        }
        setStatus("submit-status", successMessage());
        const target = redirectTarget(commandName, recordId, defaults);
        if (target) {
          window.setTimeout(() => {
            window.location.assign(target);
          }, 500);
        }
      }
    } catch (error) {
      setStatus("submit-status", `${failurePrefix()}: ${error.message}`);
    } finally {
      signSubmitButton.disabled = false;
    }
  });
}

main();
