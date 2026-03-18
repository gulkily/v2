import { loadOpenPgp } from "./openpgp_loader.js";

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
  const openpgp = await loadOpenPgp();
  const publicKey = await openpgp.readKey({ armoredKey: trimmed });
  return `openpgp:${publicKey.getFingerprint().toLowerCase()}`;
}

export async function profileHrefFromPublicKey(armoredPublicKey) {
  const identityId = await identityIdFromPublicKey(armoredPublicKey);
  return profileHrefFromIdentityId(identityId);
}

export function mergeNotificationCount(summaryText) {
  const text = typeof summaryText === "string" ? summaryText : "";
  const historicalMatches = Number((text.match(/^Historical-Match-Count:\s+(\d+)$/m) || [])[1] || 0);
  const incomingRequests = Number((text.match(/^Incoming-Request-Count:\s+(\d+)$/m) || [])[1] || 0);
  return historicalMatches + incomingRequests;
}

export async function mergeNotificationCountForIdentity(identityId, fetchImpl = globalThis.fetch) {
  const trimmed = typeof identityId === "string" ? identityId.trim() : "";
  if (!trimmed || typeof fetchImpl !== "function") {
    return 0;
  }
  const response = await fetchImpl(`/api/get_merge_management?identity_id=${encodeURIComponent(trimmed)}`);
  if (!response || !response.ok) {
    return 0;
  }
  const bodyText = await response.text();
  return mergeNotificationCount(bodyText);
}

export function storedPublicKey(storage = globalThis.localStorage) {
  if (!storage || typeof storage.getItem !== "function") {
    return "";
  }
  return storage.getItem(STORAGE_PUBLIC) || "";
}

export async function enhanceProfileNav(
  doc = globalThis.document,
  storage = globalThis.localStorage,
  fetchImpl = globalThis.fetch,
) {
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
    const identityId = await identityIdFromPublicKey(publicKey);
    const href = profileHrefFromIdentityId(identityId);
    if (!href) {
      return;
    }
    const notificationCount = await mergeNotificationCountForIdentity(identityId, fetchImpl);
    navLink.setAttribute("href", notificationCount > 0 ? `${href}/merge` : href);
    navLink.textContent = notificationCount > 0 ? `My profile (${notificationCount})` : "My profile";
    navLink.hidden = false;
  } catch (_error) {
    navLink.hidden = true;
  }
}

if (typeof document !== "undefined") {
  void enhanceProfileNav();
}
