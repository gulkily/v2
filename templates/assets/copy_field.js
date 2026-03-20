const COPY_BUTTON_SELECTOR = "[data-copy-source]";

async function copyFromSelector(selector) {
  const source = document.querySelector(selector);
  if (!source) {
    return false;
  }
  const text = "value" in source ? source.value : source.textContent || "";
  if (!text) {
    return false;
  }
  await navigator.clipboard.writeText(text);
  return true;
}

async function handleCopyClick(event) {
  const button = event.target.closest(COPY_BUTTON_SELECTOR);
  if (!(button instanceof HTMLButtonElement)) {
    return;
  }
  const selector = button.dataset.copySource;
  if (!selector || !navigator.clipboard) {
    return;
  }
  const originalLabel = button.textContent || "copy";
  try {
    const copied = await copyFromSelector(selector);
    if (!copied) {
      return;
    }
    button.dataset.copyState = "done";
    button.textContent = "copied";
    window.setTimeout(() => {
      button.dataset.copyState = "";
      button.textContent = originalLabel;
    }, 1600);
  } catch (_error) {
    button.dataset.copyState = "";
  }
}

document.addEventListener("click", (event) => {
  void handleCopyClick(event);
});
