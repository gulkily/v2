import {
  fingerprintFromIdentityId,
  identityIdFromPublicKey,
  storedPublicKey,
  syncIdentityHint,
} from "./profile_nav.js";

function canClaimUsernameFromText(bodyText) {
  const match = bodyText.match(/^Can-Claim-Username:\s+(yes|no)$/m);
  return match ? match[1] === "yes" : false;
}

function updateHrefFromText(bodyText) {
  const match = bodyText.match(/^Update-Href:\s+(.+)$/m);
  return match ? match[1].trim() : "";
}

export async function usernameClaimCtaStateForIdentity(identityId, fetchImpl = globalThis.fetch) {
  const trimmed = typeof identityId === "string" ? identityId.trim() : "";
  if (!trimmed || typeof fetchImpl !== "function") {
    return null;
  }
  const response = await fetchImpl(
    `/api/get_username_claim_cta?identity_id=${encodeURIComponent(trimmed)}`,
  );
  if (!response || !response.ok) {
    return null;
  }
  const bodyText = await response.text();
  return {
    canClaimUsername: canClaimUsernameFromText(bodyText),
    updateHref: updateHrefFromText(bodyText),
  };
}

export async function enhanceUsernameClaimCta(
  doc = globalThis.document,
  storage = globalThis.localStorage,
  fetchImpl = globalThis.fetch,
) {
  if (!doc || typeof doc.querySelector !== "function") {
    return;
  }
  const root = doc.querySelector("[data-username-claim-cta]");
  if (!root) {
    return;
  }
  const link = root.querySelector("[data-username-claim-link]");
  if (!link) {
    return;
  }
  const publicKey = storedPublicKey(storage);
  if (!publicKey) {
    try {
      await syncIdentityHint("", fetchImpl);
    } catch (_error) {
      // Ignore sync failures and fall back to a hidden banner.
    }
    root.hidden = true;
    link.setAttribute("href", "");
    return;
  }
  try {
    const identityId = await identityIdFromPublicKey(publicKey);
    await syncIdentityHint(fingerprintFromIdentityId(identityId), fetchImpl);
    const state = await usernameClaimCtaStateForIdentity(identityId, fetchImpl);
    if (!state || !state.canClaimUsername || !state.updateHref) {
      root.hidden = true;
      link.setAttribute("href", "");
      return;
    }
    link.setAttribute("href", state.updateHref);
    root.hidden = false;
  } catch (_error) {
    root.hidden = true;
  }
}

if (typeof document !== "undefined") {
  void enhanceUsernameClaimCta();
  globalThis.addEventListener?.("pageshow", () => {
    void enhanceUsernameClaimCta();
  });
}
