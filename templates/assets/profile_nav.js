import { loadOpenPgp } from "./openpgp_loader.js";

const STORAGE_PUBLIC = "forum_public_key_armored";

export function fingerprintFromIdentityId(identityId) {
  const trimmed = typeof identityId === "string" ? identityId.trim().toLowerCase() : "";
  return trimmed.startsWith("openpgp:") ? trimmed.slice("openpgp:".length) : "";
}

export async function syncIdentityHint(fingerprint, fetchImpl = globalThis.fetch) {
  if (typeof fetchImpl !== "function") {
    return false;
  }
  const trimmed = typeof fingerprint === "string" ? fingerprint.trim() : "";
  const payload = trimmed ? { fingerprint: trimmed } : {};
  const response = await fetchImpl("/api/set_identity_hint", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return Boolean(response && response.ok);
}

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
    try {
      await syncIdentityHint("", fetchImpl);
    } catch (_error) {
      // Ignore sync failures and leave the unresolved slot untouched.
    }
    return;
  }
  try {
    const identityId = await identityIdFromPublicKey(publicKey);
    await syncIdentityHint(fingerprintFromIdentityId(identityId), fetchImpl);
    const href = profileHrefFromIdentityId(identityId);
    if (!href) {
      return;
    }
    const mergeEnabled = navLink.attributes?.["data-merge-feature-enabled"] === "1"
      || navLink["data-merge-feature-enabled"] === "1";
    const notificationCount = mergeEnabled
      ? await mergeNotificationCountForIdentity(identityId, fetchImpl)
      : 0;
    navLink.setAttribute("href", notificationCount > 0 ? `${href}/merge` : `${href}?self=1`);
    navLink.textContent = notificationCount > 0 ? `My profile (${notificationCount})` : "My profile";
    navLink.removeAttribute("aria-disabled");
    navLink.removeAttribute("tabindex");
    navLink.setAttribute("data-profile-nav-state", "resolved");
  } catch (_error) {
    navLink.setAttribute("data-profile-nav-state", "unresolved");
  }
}

if (typeof document !== "undefined") {
  void enhanceProfileNav();
}
