const PREFETCHABLE_PRIMARY_NAV_HREFS = new Set(["/", "/activity/", "/tasks"]);

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

export function canPrefetchPrimaryNavHref(href) {
  return PREFETCHABLE_PRIMARY_NAV_HREFS.has(typeof href === "string" ? href : "");
}

export function prefetchPrimaryNavHref(href, doc = globalThis.document) {
  if (!canPrefetchPrimaryNavHref(href)) {
    return false;
  }
  if (!doc || !doc.head || typeof doc.createElement !== "function") {
    return false;
  }
  const existingSelector = `link[rel="prefetch"][href="${href}"]`;
  if (typeof doc.querySelector === "function" && doc.querySelector(existingSelector)) {
    return false;
  }
  const hint = doc.createElement("link");
  if (!hint || typeof hint.setAttribute !== "function") {
    return false;
  }
  hint.setAttribute("rel", "prefetch");
  hint.setAttribute("href", href);
  hint.setAttribute("as", "document");
  if (typeof doc.head.appendChild !== "function") {
    return false;
  }
  doc.head.appendChild(hint);
  return true;
}

export function prefetchPrimaryNavLink(link, doc = globalThis.document) {
  if (!isNavigablePrimaryNavLink(link)) {
    return false;
  }
  return prefetchPrimaryNavHref(link.getAttribute("href") || "", doc);
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
  const prefetchHandler = (event) => {
    const target = event?.target;
    if (!target || typeof target.closest !== "function") {
      return;
    }
    const link = target.closest("[data-primary-nav-link]");
    prefetchPrimaryNavLink(link, doc);
  };
  navRoot.addEventListener("pointerenter", prefetchHandler, true);
  navRoot.addEventListener("focusin", prefetchHandler);
  return true;
}

if (typeof document !== "undefined") {
  enhancePrimaryNav();
}
