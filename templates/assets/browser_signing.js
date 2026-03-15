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

function normalizeBoardTags(text) {
  return text.trim().split(/\s+/).filter(Boolean).join(" ");
}

function requiredTrimmed(value, fieldName) {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error(`${fieldName} is required`);
  }
  return trimmed;
}

function buildCanonicalPayload(form, commandName) {
  const postId = requiredTrimmed(form.postId.value, "Post-ID");
  const boardTags = normalizeBoardTags(requiredTrimmed(form.boardTags.value, "Board-Tags"));
  const subject = form.subject.value.trim();
  const threadId = form.threadId.value.trim();
  const parentId = form.parentId.value.trim();
  const body = normalizeNewlines(form.body.value);

  ensureAscii(postId, "Post-ID");
  ensureAscii(boardTags, "Board-Tags");
  ensureAscii(subject, "Subject");
  ensureAscii(threadId, "Thread-ID");
  ensureAscii(parentId, "Parent-ID");
  ensureAscii(body, "Body");

  const headers = [
    `Post-ID: ${postId}`,
    `Board-Tags: ${boardTags}`,
  ];
  if (subject) {
    headers.push(`Subject: ${subject}`);
  }

  if (commandName === "create_reply") {
    headers.push(`Thread-ID: ${requiredTrimmed(threadId, "Thread-ID")}`);
    headers.push(`Parent-ID: ${requiredTrimmed(parentId, "Parent-ID")}`);
  } else {
    if (threadId || parentId) {
      throw new Error("Thread-ID and Parent-ID must be blank for a new thread");
    }
  }

  return `${headers.join("\n")}\n\n${body.replace(/\n*$/, "")}\n`;
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

function formState() {
  return {
    postId: $("post-id-input"),
    boardTags: $("board-tags-input"),
    subject: $("subject-input"),
    threadId: $("thread-id-input"),
    parentId: $("parent-id-input"),
    body: $("body-input"),
  };
}

async function main() {
  const root = $("compose-app");
  if (!root) {
    return;
  }

  const commandName = root.dataset.command || "create_thread";
  const endpoint = root.dataset.endpoint || "/api/create_thread";
  const dryRun = root.dataset.dryRun === "true";
  const state = formState();
  const privateKeyInput = $("private-key-input");
  const publicKeyOutput = $("public-key-output");
  const signatureOutput = $("signature-output");
  const responseOutput = $("response-output");
  const signSubmitButton = $("sign-submit-button");

  const stored = loadKeys();
  privateKeyInput.value = stored.privateKey;
  publicKeyOutput.value = stored.publicKey;
  if (stored.privateKey && stored.publicKey) {
    setStatus("key-status", "Loaded stored local keypair.");
  }

  $("generate-key-button").addEventListener("click", async () => {
    setStatus("key-status", "Generating keypair...");
    try {
      const generated = await generateKeypair();
      privateKeyInput.value = generated.privateKey;
      publicKeyOutput.value = generated.publicKey;
      saveKeys(generated.privateKey, generated.publicKey);
      setStatus("key-status", "Generated and stored a new local OpenPGP keypair.");
    } catch (error) {
      setStatus("key-status", `Key generation failed: ${error.message}`);
    }
  });

  $("import-key-button").addEventListener("click", async () => {
    setStatus("key-status", "Importing key...");
    try {
      const privateKey = requiredTrimmed(privateKeyInput.value, "private key");
      ensureAscii(privateKey, "private key");
      const publicKey = await privateToPublic(privateKey);
      publicKeyOutput.value = publicKey;
      saveKeys(privateKey, publicKey);
      setStatus("key-status", "Imported and stored the local private key.");
    } catch (error) {
      setStatus("key-status", `Key import failed: ${error.message}`);
    }
  });

  $("signed-post-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    signSubmitButton.disabled = true;
    setStatus("submit-status", "Signing payload...");
    responseOutput.value = "";
    signatureOutput.value = "";

    try {
      const privateKey = requiredTrimmed(privateKeyInput.value, "private key");
      const publicKey = requiredTrimmed(publicKeyOutput.value, "public key");
      const payload = buildCanonicalPayload(state, commandName);
      const signature = await signPayload(payload, privateKey);

      signatureOutput.value = signature;
      setStatus("submit-status", dryRun ? "Submitting signed dry-run request..." : "Submitting signed post...");

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          payload,
          signature,
          public_key: publicKey,
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
        setStatus("submit-status", "Signed dry-run request accepted.");
      } else {
        setStatus("submit-status", "Signed post accepted. Redirecting to the new post...");
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
