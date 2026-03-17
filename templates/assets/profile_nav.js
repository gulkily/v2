import * as openpgp from "./vendor/openpgp.min.mjs";

const STORAGE_PUBLIC = "forum_public_key_armored";

export function profileHrefFromIdentityId(identityId) {
  const trimmed = typeof identityId === "string" ? identityId.trim().toLowerCase() : "";
  if (!trimmed.startsWith("openpgp:")) {
    return "";
  }
  return `/profiles/${trimmed.replace(":", "-")}`;
}

export async function identityIdFromPublicKey(armoredPublicKey) {
  const trimmed = typeof armoredPublicKey === "string" ? armoredPublicKey.trim() : "";
  if (!trimmed) {
    return "";
  }
  const publicKey = await openpgp.readKey({ armoredKey: trimmed });
  return `openpgp:${publicKey.getFingerprint().toLowerCase()}`;
}

export async function profileHrefFromPublicKey(armoredPublicKey) {
  const identityId = await identityIdFromPublicKey(armoredPublicKey);
  return profileHrefFromIdentityId(identityId);
}

export function storedPublicKey(storage = globalThis.localStorage) {
  if (!storage || typeof storage.getItem !== "function") {
    return "";
  }
  return storage.getItem(STORAGE_PUBLIC) || "";
}

export async function enhanceProfileNav(doc = globalThis.document, storage = globalThis.localStorage) {
  if (!doc || typeof doc.querySelector !== "function") {
    return;
  }
  const navLink = doc.querySelector("[data-profile-nav-link]");
  if (!navLink) {
    return;
  }
  const publicKey = storedPublicKey(storage);
  if (!publicKey) {
    return;
  }
  try {
    const href = await profileHrefFromPublicKey(publicKey);
    if (!href) {
      return;
    }
    navLink.setAttribute("href", href);
    navLink.hidden = false;
  } catch (_error) {
    navLink.hidden = true;
  }
}

if (typeof document !== "undefined") {
  void enhanceProfileNav();
}
