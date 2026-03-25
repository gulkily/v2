import {
  classifyOpenPgpError,
  describeOpenPgpFailure,
  loadOpenPgp,
} from "./openpgp_loader.js";

const STORAGE_PRIVATE = "forum_private_key_armored";
const STORAGE_PUBLIC = "forum_public_key_armored";
const STORAGE_DRAFT_PREFIX = "forum_compose_draft_v1:";
const STORAGE_PENDING_PREFIX = "forum_pending_submission_v1:";
const DRAFT_SAVE_DELAY_MS = 400;

function signingDebugEnabled() {
  try {
    const pageFlag = globalThis.document?.querySelector?.("[data-signing-debug-enabled='true']");
    if (pageFlag) {
      return true;
    }
  } catch (_error) {
    // Ignore DOM lookup failures and fall back to local storage.
  }
  try {
    return globalThis.localStorage?.getItem("forum_debug_signing") === "1";
  } catch (_error) {
    return false;
  }
}

function logSigningDebug(event, details = {}) {
  if (!signingDebugEnabled()) {
    return;
  }
  try {
    console.warn("[browser_signing]", event, details);
  } catch (_error) {
    // Ignore console failures in restricted environments.
  }
}

function $(id) {
  return document.getElementById(id);
}

function applyStatusUpdate(element, message, { tone } = {}) {
  if (element) {
    element.textContent = message;
    if (typeof tone === "string" && tone) {
      element.dataset.statusTone = tone;
    }
  }
}

function setStatus(id, message, options = {}) {
  applyStatusUpdate($(id), message, options);
}

function setSubmitStatus(message, { tone = "idle" } = {}) {
  setStatus("submit-status", message, { tone });
}

function setActiveSubmitStatus(message) {
  setSubmitStatus(message, { tone: "active" });
}

function setButtonLabel(button, label) {
  if (button && typeof label === "string" && label) {
    button.textContent = label;
  }
}

function requiresSigningSubmitLabel(commandName, { dryRun = false } = {}) {
  if (dryRun) {
    return "Signing required for preview";
  }
  if (commandName === "update_profile") {
    return "Signing required for update";
  }
  return "Signing required to submit";
}

function normalizeNewlines(text) {
  return text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

const ASCII_COMPOSE_REPLACEMENTS = new Map([
  ["\u2018", "'"],
  ["\u2019", "'"],
  ["\u201C", '"'],
  ["\u201D", '"'],
  ["\u2013", "-"],
  ["\u2014", "-"],
  ["\u2026", "..."],
  ["\u00A0", " "],
]);

function unsupportedComposeCharacters(text) {
  const characters = [];
  for (const character of text) {
    if (!/^[\x00-\x7F]$/.test(character)) {
      characters.push(character);
    }
  }
  return characters;
}

function normalizeComposeAscii(text, { removeUnsupported = false } = {}) {
  let normalized = "";
  let hadCorrections = false;
  for (const character of normalizeNewlines(text)) {
    const replacement = ASCII_COMPOSE_REPLACEMENTS.get(character);
    if (replacement !== undefined) {
      normalized += replacement;
      hadCorrections = true;
      continue;
    }
    normalized += character;
  }

  const unsupportedBeforeRemoval = unsupportedComposeCharacters(normalized);
  if (removeUnsupported && unsupportedBeforeRemoval.length) {
    normalized = Array.from(normalized)
      .filter((character) => /^[\x00-\x7F]$/.test(character))
      .join("");
  }

  return {
    text: normalized,
    hadCorrections,
    unsupportedCount: removeUnsupported ? 0 : unsupportedBeforeRemoval.length,
    removedUnsupportedCount: removeUnsupported ? unsupportedBeforeRemoval.length : 0,
  };
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
  const openpgp = await loadOpenPgp();
  const privateKey = await openpgp.readPrivateKey({ armoredKey: armoredPrivateKey });
  return privateKey.toPublic().armor();
}

async function publicKeyFingerprint(armoredPublicKey) {
  const openpgp = await loadOpenPgp();
  const publicKey = await openpgp.readKey({ armoredKey: armoredPublicKey });
  return publicKey.getFingerprint().toUpperCase();
}

async function signPayload(payloadText, armoredPrivateKey) {
  const openpgp = await loadOpenPgp();
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
  const openpgp = await loadOpenPgp();
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
  if (value.length < 3) {
    throw new Error("Display-Name must be at least 3 characters");
  }
  if (value.length > 32) {
    throw new Error("Display-Name must be at most 32 characters");
  }
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value)) {
    throw new Error("Display-Name must use lowercase ASCII letters, digits, and single hyphens only");
  }
  if (new Set(["activity", "admin", "api", "assets", "compose", "instance", "profiles", "threads", "user"]).has(value)) {
    throw new Error("Display-Name is reserved");
  }
  return value;
}

function buildCanonicalPostPayload(form, commandName, defaults, { proofOfWork = "", postId = "" } = {}) {
  const body = normalizeComposeAscii(requiredTrimmed(form.body.value, "Body")).text.replace(/\n*$/, "\n");
  const resolvedPostId = postId || generatePostId(commandName, body);
  const boardTags = requiredTrimmed(defaults.boardTags, "Board-Tags");
  const subject = commandName === "create_thread" ? deriveSubjectFromBody(body) : "";
  const threadType = defaults.threadType ? normalizeSingleLineAscii(defaults.threadType, "Thread-Type") : "";

  ensureAscii(resolvedPostId, "Post-ID");
  ensureAscii(boardTags, "Board-Tags");
  ensureAscii(subject, "Subject");
  ensureAscii(defaults.threadId, "Thread-ID");
  ensureAscii(defaults.parentId, "Parent-ID");
  ensureAscii(body, "Body");

  const headers = [
    `Post-ID: ${resolvedPostId}`,
    `Board-Tags: ${boardTags}`,
  ];
  if (subject) {
    headers.push(`Subject: ${subject}`);
  }
  if (proofOfWork) {
    headers.push(`Proof-Of-Work: ${normalizeSingleLineAscii(proofOfWork, "Proof-Of-Work")}`);
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
    postId: resolvedPostId,
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

function pendingSubmissionStorageKey(commandName, defaults, { dryRun = false } = {}) {
  const scopeParts = [commandName, dryRun ? "dry-run" : "publish"];
  if (commandName === "update_profile") {
    scopeParts.push(defaults.sourceIdentityId || "");
    scopeParts.push(defaults.profileSlug || "");
  } else {
    scopeParts.push(defaults.threadType || "plain");
    scopeParts.push(defaults.boardTags || "general");
    scopeParts.push(defaults.threadId || "");
    scopeParts.push(defaults.parentId || "");
  }
  return `${STORAGE_PENDING_PREFIX}${scopeParts.join("|")}`;
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

function loadPendingSubmission(storageKey) {
  try {
    const rawValue = localStorage.getItem(storageKey);
    if (!rawValue) {
      return null;
    }
    const parsed = JSON.parse(rawValue);
    if (!parsed || typeof parsed !== "object" || typeof parsed.payload !== "string") {
      return null;
    }
    return parsed;
  } catch (_error) {
    return null;
  }
}

function savePendingSubmission(storageKey, pending) {
  localStorage.setItem(storageKey, JSON.stringify(pending));
  return pending;
}

function clearPendingSubmission(storageKey) {
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

function updateComposeNormalizationStatus(message) {
  setStatus("compose-normalization-status", message);
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

async function fetchPowRequirement(signerFingerprint) {
  const response = await fetch("/api/pow_requirement", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      signer_fingerprint: signerFingerprint,
    }),
  });
  if (!response.ok) {
    const responseText = await response.text();
    throw new Error(responseText.trim() || `PoW requirement lookup failed with status ${response.status}`);
  }
  const payload = await response.json();
  if (!payload || typeof payload !== "object") {
    throw new Error("PoW requirement lookup returned an invalid response");
  }
  return {
    required: payload.required === true,
    difficulty: Number.isInteger(payload.difficulty) ? payload.difficulty : 0,
    signerFingerprint: typeof payload.signer_fingerprint === "string" ? payload.signer_fingerprint : "",
  };
}

function formatSigningStatus(commandName, error, { allowUnsignedFallback = false } = {}) {
  const baseMessage = describeOpenPgpFailure(error);
  if (allowUnsignedFallback) {
    return `${baseMessage} Posting can still continue unsigned.`;
  }
  if (commandName === "update_profile") {
    return `${baseMessage} Profile updates still require a working signing key.`;
  }
  return `${baseMessage} Unsigned fallback is disabled here, so signing is still required.`;
}

function formatFallbackSubmitStatus(error) {
  return `${describeOpenPgpFailure(error)} Submitting unsigned post instead...`;
}

function formatPendingSubmissionStatus(savedAt) {
  const formatted = formatSavedAt(savedAt);
  if (formatted) {
    return `A previous submission attempt is still saved locally from ${formatted}.`;
  }
  return "A previous submission attempt is still saved locally in this browser.";
}

function errorMessage(error) {
  if (error && typeof error.message === "string" && error.message) {
    return error.message;
  }
  return String(error);
}

logSigningDebug("module_loaded", {
  hasDocument: typeof document !== "undefined",
  locationHref: globalThis.location?.href || "",
});

function responseMessageText(responseText) {
  const trimmed = typeof responseText === "string" ? responseText.trim() : "";
  if (!trimmed) {
    return "";
  }
  const messageMatch = trimmed.match(/^Message:\s+(.+)$/m);
  if (messageMatch) {
    return messageMatch[1].trim();
  }
  return trimmed;
}

async function main() {
  logSigningDebug("main_enter");
  const root = $("compose-app") || $("profile-update-app");
  if (!root) {
    logSigningDebug("main_no_root", {
      hasComposeApp: Boolean($("compose-app")),
      hasProfileUpdateApp: Boolean($("profile-update-app")),
    });
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
  const clearPendingSubmissionButton = $("clear-pending-submission-button");
  const normalizationActions = $("compose-normalization-actions");
  const removeUnsupportedButton = $("remove-unsupported-button");
  const draftContext = composeDraftContext(commandName, defaults);
  const canStoreDraft = Boolean(draftContext) && draftStorageAvailable();
  const pendingSubmissionKey = pendingSubmissionStorageKey(commandName, defaults, { dryRun });
  const canStorePendingSubmission = commandName !== "update_profile" && draftStorageAvailable() && !dryRun;
  const allowUnsignedFallback = root.dataset.unsignedFallbackEnabled === "true";
  let currentKeys = null;
  let pendingDraftTimer = 0;

  logSigningDebug("main_root_found", {
    rootId: root.id || "",
    commandName,
    endpoint,
    dryRun,
    allowUnsignedFallback,
    signingDebugEnabled: root.dataset.signingDebugEnabled === "true",
  });

  if (
    !form
    || !privateKeyInput
    || !publicKeyOutput
    || !payloadOutput
    || !signatureOutput
    || !responseOutput
    || !signSubmitButton
  ) {
    logSigningDebug("main_missing_required_elements", {
      hasForm: Boolean(form),
      hasPrivateKeyInput: Boolean(privateKeyInput),
      hasPublicKeyOutput: Boolean(publicKeyOutput),
      hasPayloadOutput: Boolean(payloadOutput),
      hasSignatureOutput: Boolean(signatureOutput),
      hasResponseOutput: Boolean(responseOutput),
      hasSignSubmitButton: Boolean(signSubmitButton),
    });
    return;
  }

  logSigningDebug("main_required_elements_ready", {
    hasClearPendingSubmissionButton: Boolean(clearPendingSubmissionButton),
    hasRemoveUnsupportedButton: Boolean(removeUnsupportedButton),
    canStoreDraft,
    canStorePendingSubmission,
  });

  function defaultSubmitLabel() {
    if (dryRun) {
      return "Submit preview";
    }
    return commandName === "update_profile" ? "Submit update" : "Submit post";
  }

  function signedSubmitLabel() {
    return dryRun ? "Sign and preview" : "Sign and submit";
  }

  function unsignedSubmitLabel() {
    if (dryRun) {
      return "Submit preview";
    }
    return commandName === "update_profile" ? "Submit update" : "Submit without signing";
  }

  function applySubmitLabel(mode = "default") {
    if (mode === "signed") {
      setButtonLabel(signSubmitButton, signedSubmitLabel());
      return;
    }
    if (mode === "unsigned") {
      setButtonLabel(signSubmitButton, unsignedSubmitLabel());
      return;
    }
    if (mode === "requires-signing") {
      setButtonLabel(signSubmitButton, requiresSigningSubmitLabel(commandName, { dryRun }));
      return;
    }
    setButtonLabel(signSubmitButton, defaultSubmitLabel());
  }

  function idleDraftStatus() {
    if (draftContext && canStoreDraft) {
      return "Drafts are saved locally in this browser.";
    }
    return "No saved submission is currently stored in this browser.";
  }

  function setPendingSubmissionButtonVisible(visible) {
    if (clearPendingSubmissionButton) {
      clearPendingSubmissionButton.hidden = !visible;
    }
  }

  applySubmitLabel("default");

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
  } else {
    setDraftStatus(idleDraftStatus());
  }
  if (canStorePendingSubmission) {
    const pendingSubmission = loadPendingSubmission(pendingSubmissionKey);
    if (pendingSubmission) {
      setDraftStatus(formatPendingSubmissionStatus(pendingSubmission.savedAt));
      setPendingSubmissionButtonVisible(true);
    }
  }

  if (commandName === "update_profile" && state.displayName) {
    state.displayName.addEventListener("focus", () => {
      state.displayName.select();
    });
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
          setDraftStatus(idleDraftStatus());
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

  if (clearPendingSubmissionButton) {
    clearPendingSubmissionButton.addEventListener("click", () => {
      clearPendingSubmission(pendingSubmissionKey);
      setPendingSubmissionButtonVisible(false);
      responseOutput.value = "";
      setDraftStatus(idleDraftStatus());
      setSubmitStatus("Cleared the saved local submission snapshot.");
    });
  }

  function applyKeys(keys) {
    currentKeys = keys;
    privateKeyInput.value = keys.privateKey;
    publicKeyOutput.value = keys.publicKey;
    applySubmitLabel("signed");
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
    logSigningDebug("prepare_initial_keys_start", {
      commandName,
    });
    if (commandName === "update_profile") {
      const stored = await deriveStoredKeys();
      if (!stored) {
        logSigningDebug("prepare_initial_keys_no_stored_profile_key");
        setStatus(
          "key-status",
          "Import the private key for this profile, or generate a new one only if it matches this identity.",
        );
        return null;
      }
      applyKeys(stored);
      setStatus("key-status", "Loaded the stored local signing key.");
      logSigningDebug("prepare_initial_keys_loaded_profile_key");
      return stored;
    }
    const keys = await prepareKeys({}, "Local signing key is ready.");
    logSigningDebug("prepare_initial_keys_ready", {
      hasPublicKey: Boolean(keys?.publicKey),
    });
    return keys;
  }

  async function resolveSubmitKeys() {
    logSigningDebug("resolve_submit_keys_start", {
      commandName,
      hasCurrentKeys: Boolean(currentKeys),
    });
    if (currentKeys) {
      logSigningDebug("resolve_submit_keys_using_cached_keys");
      return currentKeys;
    }
    if (commandName === "update_profile") {
      const stored = await deriveStoredKeys();
      if (stored) {
        applyKeys(stored);
        logSigningDebug("resolve_submit_keys_loaded_profile_key");
        return stored;
      }
      logSigningDebug("resolve_submit_keys_missing_profile_key");
      throw new Error("Load or import the private key for this profile before signing.");
    }
    const keys = await ensureLocalKeys();
    applyKeys(keys);
    logSigningDebug("resolve_submit_keys_generated_or_loaded_keys", {
      hasPublicKey: Boolean(keys.publicKey),
    });
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
    return commandName === "update_profile" ? "Username update failed" : "Signed posting failed";
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

  function unsignedSuccessMessage() {
    if (dryRun) {
      return "Unsigned preview accepted.";
    }
    return "Unsigned post accepted. Redirecting. It may be reviewed by moderation.";
  }

  async function submitPayload({ payload, signature = "", publicKey = "" }) {
    const requestBody = {
      payload,
      dry_run: dryRun,
    };
    if (signature && publicKey) {
      requestBody.signature = signature;
      requestBody.public_key = publicKey;
    }
    return fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });
  }

  function normalizeBodyInput({ removeUnsupported = false } = {}) {
    if (!state.body) {
      return { text: "", hadCorrections: false, unsupportedCount: 0, removedUnsupportedCount: 0 };
    }
    const result = normalizeComposeAscii(state.body.value, { removeUnsupported });
    if (state.body.value !== result.text) {
      state.body.value = result.text;
    }
    if (result.removedUnsupportedCount > 0) {
      updateComposeNormalizationStatus(
        `Removed ${result.removedUnsupportedCount} unsupported character${result.removedUnsupportedCount === 1 ? "" : "s"} from the message.`,
      );
    } else if (result.unsupportedCount > 0) {
      updateComposeNormalizationStatus(
        `Unsupported characters remain in the message. Remove them before signing.`,
      );
    } else if (result.hadCorrections) {
      updateComposeNormalizationStatus("Converted common non-ASCII punctuation to ASCII.");
    } else {
      updateComposeNormalizationStatus("");
    }
    if (normalizationActions) {
      normalizationActions.hidden = result.unsupportedCount === 0;
    }
    if (removeUnsupportedButton) {
      removeUnsupportedButton.disabled = result.unsupportedCount === 0;
    }
    return result;
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
      if (input === state.body) {
        normalizeBodyInput();
      }
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
      const classified = classifyOpenPgpError(error);
      setStatus("key-status", formatSigningStatus(commandName, classified, { allowUnsignedFallback }));
      if (!allowUnsignedFallback) {
        applySubmitLabel("requires-signing");
      }
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
      const classified = classifyOpenPgpError(error);
      setStatus("key-status", formatSigningStatus(commandName, classified, { allowUnsignedFallback }));
      if (!allowUnsignedFallback) {
        applySubmitLabel("requires-signing");
      }
    }
  });

  if (removeUnsupportedButton) {
    removeUnsupportedButton.addEventListener("click", () => {
      normalizeBodyInput({ removeUnsupported: true });
      updatePayloadPreview(state, commandName, defaults);
      signatureOutput.value = "";
      responseOutput.value = "";
      scheduleDraftSave();
    });
  }

  if (state.body) {
    normalizeBodyInput();
  }
  updatePayloadPreview(state, commandName, defaults);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    logSigningDebug("submit_start", {
      commandName,
      dryRun,
    });
    signSubmitButton.disabled = true;
    setActiveSubmitStatus("Building canonical payload...");
    responseOutput.value = "";
    signatureOutput.value = "";

    try {
      normalizeBodyInput();
      let built = buildCanonicalPayload(state, commandName, defaults);
      let signature = "";
      let publicKey = "";
      let usedUnsignedFallback = false;
      if (commandName === "update_profile") {
        const keys = await resolveSubmitKeys();
        payloadOutput.value = built.payload;
        if (canStorePendingSubmission) {
            savePendingSubmission(pendingSubmissionKey, {
              commandName,
              endpoint,
              payload: built.payload,
              recordId: built.recordId || built.postId || "",
              savedAt: new Date().toISOString(),
              attemptedSignedSubmit: true,
            });
            setPendingSubmissionButtonVisible(true);
          }
        setActiveSubmitStatus("Signing payload...");
        logSigningDebug("submit_sign_profile_payload");
        signature = await signPayload(built.payload, keys.privateKey);
        publicKey = keys.publicKey;
        signatureOutput.value = signature;
      } else {
        try {
          const keys = await resolveSubmitKeys();
          if (defaults.powEnabled) {
            setActiveSubmitStatus("Checking whether proof-of-work is required...");
            logSigningDebug("submit_check_pow_requirement");
            const signerFingerprint = await publicKeyFingerprint(keys.publicKey);
            const requirement = await fetchPowRequirement(signerFingerprint);
            if (requirement.required) {
              setActiveSubmitStatus(`Computing proof-of-work (${requirement.difficulty} leading zero bits)...`);
              logSigningDebug("submit_pow_required", {
                difficulty: requirement.difficulty,
              });
              const proofOfWork = await solveProofOfWork({
                fingerprint: requirement.signerFingerprint,
                postId: built.postId,
                difficulty: requirement.difficulty,
                onProgress: (attempts) => {
                  setActiveSubmitStatus(
                    `Computing proof-of-work (${requirement.difficulty} leading zero bits, ${attempts} attempts)...`,
                  );
                },
              });
              built = buildCanonicalPostPayload(state, commandName, defaults, {
                proofOfWork,
                postId: built.postId,
              });
            }
          }
          payloadOutput.value = built.payload;
          if (canStorePendingSubmission) {
            savePendingSubmission(pendingSubmissionKey, {
              commandName,
              endpoint,
              payload: built.payload,
              recordId: built.recordId || built.postId || "",
              savedAt: new Date().toISOString(),
              attemptedSignedSubmit: true,
            });
            setDraftStatus("Saved the current submission locally until the server confirms it.");
            setPendingSubmissionButtonVisible(true);
          }
          setActiveSubmitStatus("Signing payload...");
          logSigningDebug("submit_sign_post_payload");
          signature = await signPayload(built.payload, keys.privateKey);
          publicKey = keys.publicKey;
          signatureOutput.value = signature;
        } catch (error) {
          const classified = classifyOpenPgpError(error);
          logSigningDebug("submit_signing_path_failed", {
            message: errorMessage(classified),
            code: classified.code || "",
          });
          if (!allowUnsignedFallback) {
            throw classified;
          }
          usedUnsignedFallback = true;
          applySubmitLabel("unsigned");
          payloadOutput.value = built.payload;
          if (canStorePendingSubmission) {
            savePendingSubmission(pendingSubmissionKey, {
              commandName,
              endpoint,
              payload: built.payload,
              recordId: built.recordId || built.postId || "",
              savedAt: new Date().toISOString(),
              attemptedSignedSubmit: false,
            });
            setDraftStatus("Saved the current submission locally until the server confirms it.");
            setPendingSubmissionButtonVisible(true);
          }
          signatureOutput.value = "";
          setStatus("key-status", formatSigningStatus(commandName, classified, { allowUnsignedFallback }));
          setActiveSubmitStatus(formatFallbackSubmitStatus(classified));
        }
      }

      if (!usedUnsignedFallback) {
        setActiveSubmitStatus(submittingMessage());
      }

      const response = await submitPayload({
        payload: built.payload,
        signature,
        publicKey,
      });
      logSigningDebug("submit_request_sent", {
        commandName,
      });
      const responseText = await response.text();
      responseOutput.value = responseText;

      if (!response.ok) {
        logSigningDebug("submit_response_not_ok", {
          status: response.status,
          message: responseMessageText(responseText),
        });
        throw new Error(responseMessageText(responseText) || `Request failed with status ${response.status}`);
      }

      const recordId = responseRecordId(responseText);
      if (dryRun) {
        setSubmitStatus(usedUnsignedFallback ? unsignedSuccessMessage() : successMessage());
      } else {
        if (draftContext && canStoreDraft) {
          window.clearTimeout(pendingDraftTimer);
          clearDraft(draftContext.storageKey);
          setDraftStatus("Local draft cleared after successful submission.");
        }
        if (canStorePendingSubmission) {
          clearPendingSubmission(pendingSubmissionKey);
          setPendingSubmissionButtonVisible(false);
        }
        setSubmitStatus(usedUnsignedFallback ? unsignedSuccessMessage() : successMessage());
        const target = redirectTarget(commandName, recordId, defaults);
        if (target) {
          window.setTimeout(() => {
            window.location.assign(target);
          }, 500);
        }
      }
    } catch (error) {
      logSigningDebug("submit_failed", {
        message: errorMessage(error),
      });
      setSubmitStatus(`${failurePrefix()}: ${errorMessage(error)}`);
    } finally {
      logSigningDebug("submit_finished");
      signSubmitButton.disabled = false;
    }
  });

  setStatus("key-status", "Checking browser signing support...");
  logSigningDebug("prepare_initial_keys_dispatch");
  void prepareInitialKeys().catch((error) => {
    const classified = classifyOpenPgpError(error);
    logSigningDebug("prepare_initial_keys_failed", {
      message: errorMessage(classified),
      code: classified.code || "",
    });
    setStatus("key-status", formatSigningStatus(commandName, classified, { allowUnsignedFallback }));
    if (allowUnsignedFallback) {
      applySubmitLabel("unsigned");
    } else {
      applySubmitLabel("requires-signing");
    }
  });
}

if (typeof document !== "undefined") {
  logSigningDebug("main_dispatch");
  main();
}

export {
  applyStatusUpdate,
  ensureLocalKeys,
  formatSigningStatus,
  normalizeComposeAscii,
  pendingSubmissionStorageKey,
  publicKeyFingerprint,
  responseMessageText,
  requiresSigningSubmitLabel,
};
