const STORAGE_PREFIX = "forum_merge_suggestion_dismissed:";

export function mergeSuggestionKey(identityId, otherIdentityId) {
  const left = typeof identityId === "string" ? identityId.trim().toLowerCase() : "";
  const right = typeof otherIdentityId === "string" ? otherIdentityId.trim().toLowerCase() : "";
  if (!left || !right) {
    return "";
  }
  return `${STORAGE_PREFIX}${left}:${right}`;
}

export function isMergeSuggestionDismissed(storage, identityId, otherIdentityId) {
  const key = mergeSuggestionKey(identityId, otherIdentityId);
  if (!key || !storage || typeof storage.getItem !== "function") {
    return false;
  }
  return storage.getItem(key) === "1";
}

export function dismissMergeSuggestion(storage, identityId, otherIdentityId) {
  const key = mergeSuggestionKey(identityId, otherIdentityId);
  if (!key || !storage || typeof storage.setItem !== "function") {
    return false;
  }
  storage.setItem(key, "1");
  return true;
}

export function enhanceMergeSuggestion(doc = globalThis.document, storage = globalThis.localStorage) {
  if (!doc || typeof doc.querySelectorAll !== "function") {
    return;
  }
  const sections = doc.querySelectorAll("[data-merge-suggestion]");
  for (const section of sections) {
    const identityId = section.getAttribute("data-identity-id") || "";
    const otherIdentityId = section.getAttribute("data-other-identity-id") || "";
    if (isMergeSuggestionDismissed(storage, identityId, otherIdentityId)) {
      section.hidden = true;
      continue;
    }
    const dismissButton = section.querySelector("[data-dismiss-merge-suggestion]");
    if (!dismissButton || typeof dismissButton.addEventListener !== "function") {
      continue;
    }
    dismissButton.hidden = false;
    dismissButton.addEventListener("click", () => {
      if (dismissMergeSuggestion(storage, identityId, otherIdentityId)) {
        section.hidden = true;
      }
    });
  }
}

if (typeof document !== "undefined") {
  enhanceMergeSuggestion();
}
