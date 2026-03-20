const STORAGE_PRIVATE = "forum_private_key_armored";
const STORAGE_PUBLIC = "forum_public_key_armored";

function $(id) {
  return document.getElementById(id);
}

function firstElement(ids) {
  for (const id of ids) {
    const element = $(id);
    if (element) {
      return element;
    }
  }
  return null;
}

function storedValue(storage, key) {
  if (!storage || typeof storage.getItem !== "function") {
    return "";
  }
  return storage.getItem(key) || "";
}

function setValue(ids, value) {
  const element = firstElement(ids);
  if (element) {
    element.value = value;
  }
}

function setStatus(message) {
  const element = firstElement(["key-material-status", "profile-key-status"]);
  if (element) {
    element.textContent = message;
  }
}

export function enhanceProfileKeyViewer(storage = globalThis.localStorage) {
  const privateKey = storedValue(storage, STORAGE_PRIVATE);
  const publicKey = storedValue(storage, STORAGE_PUBLIC);
  setValue(["key-private-key-output", "profile-private-key-output"], privateKey);
  setValue(["key-public-key-output", "profile-public-key-output"], publicKey);

  if (privateKey) {
    setStatus("Showing the browser-stored signing key for this device.");
    return;
  }
  if (publicKey) {
    setStatus("A public key is saved in this browser, but the private key is not available here.");
    return;
  }
  setStatus("No browser-stored signing key is available on this device.");
}

if (typeof document !== "undefined") {
  enhanceProfileKeyViewer();
}
