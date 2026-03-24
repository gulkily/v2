import {
  fingerprintFromIdentityId,
  identityIdFromPublicKey,
  storedPublicKey,
  syncIdentityHint,
} from "./profile_nav.js";

const STORAGE_USERNAME_CLAIM_CTA = "forum_username_claim_cta";

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

export function readStoredUsernameClaimCtaState(storage = globalThis.localStorage) {
  if (!storage || typeof storage.getItem !== "function") {
    return { visible: false, updateHref: "" };
  }
  try {
    const raw = storage.getItem(STORAGE_USERNAME_CLAIM_CTA);
    if (!raw) {
      return { visible: false, updateHref: "" };
    }
    const parsed = JSON.parse(raw);
    if (!parsed || parsed.visible !== true || typeof parsed.updateHref !== "string" || !parsed.updateHref) {
      return { visible: false, updateHref: "" };
    }
    return { visible: true, updateHref: parsed.updateHref };
  } catch (_error) {
    return { visible: false, updateHref: "" };
  }
}

export function storeUsernameClaimCtaState(state, storage = globalThis.localStorage) {
  if (!storage || typeof storage.setItem !== "function" || typeof storage.removeItem !== "function") {
    return;
  }
  try {
    if (!state || state.visible !== true || typeof state.updateHref !== "string" || !state.updateHref) {
      storage.removeItem(STORAGE_USERNAME_CLAIM_CTA);
      return;
    }
    storage.setItem(
      STORAGE_USERNAME_CLAIM_CTA,
      JSON.stringify({ visible: true, updateHref: state.updateHref }),
    );
  } catch (_error) {
    // Ignore storage failures and continue with in-memory DOM updates only.
  }
}

export function applyUsernameClaimCtaState(
  state,
  doc = globalThis.document,
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
  const visible = Boolean(state && state.visible === true && typeof state.updateHref === "string" && state.updateHref);
  link.setAttribute("href", visible ? state.updateHref : "");
  doc.documentElement?.setAttribute("data-username-claim-visible", visible ? "1" : "0");
  doc.documentElement?.setAttribute("data-username-claim-href", visible ? state.updateHref : "");
}

export function applyStoredUsernameClaimCtaState(
  doc = globalThis.document,
  storage = globalThis.localStorage,
) {
  applyUsernameClaimCtaState(readStoredUsernameClaimCtaState(storage), doc);
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
  applyStoredUsernameClaimCtaState(doc, storage);
  const publicKey = storedPublicKey(storage);
  if (!publicKey) {
    try {
      await syncIdentityHint("", fetchImpl);
    } catch (_error) {
      // Ignore sync failures and fall back to a hidden banner.
    }
    storeUsernameClaimCtaState({ visible: false, updateHref: "" }, storage);
    applyUsernameClaimCtaState({ visible: false, updateHref: "" }, doc);
    return;
  }
  try {
    const identityId = await identityIdFromPublicKey(publicKey);
    await syncIdentityHint(fingerprintFromIdentityId(identityId), fetchImpl);
    const state = await usernameClaimCtaStateForIdentity(identityId, fetchImpl);
    if (!state || !state.canClaimUsername || !state.updateHref) {
      storeUsernameClaimCtaState({ visible: false, updateHref: "" }, storage);
      applyUsernameClaimCtaState({ visible: false, updateHref: "" }, doc);
      return;
    }
    const resolvedState = { visible: true, updateHref: state.updateHref };
    storeUsernameClaimCtaState(resolvedState, storage);
    applyUsernameClaimCtaState(resolvedState, doc);
  } catch (_error) {
    storeUsernameClaimCtaState({ visible: false, updateHref: "" }, storage);
    applyUsernameClaimCtaState({ visible: false, updateHref: "" }, doc);
  }
}

if (typeof document !== "undefined") {
  applyStoredUsernameClaimCtaState();
  void enhanceUsernameClaimCta();
  globalThis.addEventListener?.("pageshow", () => {
    void enhanceUsernameClaimCta();
  });
}
