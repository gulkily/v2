function eventHasModifiedNavigation(event) {
  return Boolean(
    event?.defaultPrevented
      || event?.button !== 0
      || event?.metaKey
      || event?.ctrlKey
      || event?.shiftKey
      || event?.altKey,
  );
}

function isNavigablePrimaryNavLink(link) {
  if (!link || typeof link.getAttribute !== "function") {
    return false;
  }
  const href = link.getAttribute("href") || "";
  if (!href || href.startsWith("#")) {
    return false;
  }
  if (link.getAttribute("aria-disabled") === "true") {
    return false;
  }
  const target = link.getAttribute("target") || "";
  return target === "" || target === "_self";
}

export function markPrimaryNavPending(navRoot, link) {
  if (!navRoot || !link || typeof navRoot.setAttribute !== "function" || typeof link.setAttribute !== "function") {
    return;
  }
  const pendingHref = link.getAttribute("href") || "";
  navRoot.setAttribute("data-primary-nav-pending", "true");
  navRoot.setAttribute("aria-busy", "true");
  navRoot.setAttribute("data-primary-nav-pending-href", pendingHref);
  link.setAttribute("data-primary-nav-pending", "true");
}

export function handlePrimaryNavActivation(event, navRoot) {
  if (eventHasModifiedNavigation(event)) {
    return false;
  }
  const target = event?.target;
  if (!target || typeof target.closest !== "function") {
    return false;
  }
  const link = target.closest("[data-primary-nav-link]");
  if (!isNavigablePrimaryNavLink(link)) {
    return false;
  }
  markPrimaryNavPending(navRoot, link);
  return true;
}

export function enhancePrimaryNav(doc = globalThis.document) {
  if (!doc || typeof doc.querySelector !== "function") {
    return false;
  }
  const navRoot = doc.querySelector("[data-primary-nav]");
  if (!navRoot || typeof navRoot.addEventListener !== "function") {
    return false;
  }
  navRoot.addEventListener("click", (event) => {
    handlePrimaryNavActivation(event, navRoot);
  });
  return true;
}

if (typeof document !== "undefined") {
  enhancePrimaryNav();
}
