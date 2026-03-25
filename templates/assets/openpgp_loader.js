class OpenPgpUnavailableError extends Error {
  constructor(code, message, diagnosticMessage = message) {
    super(message);
    this.name = "OpenPgpUnavailableError";
    this.code = code;
    this.diagnosticMessage = diagnosticMessage;
  }
}

let openpgpModulePromise = null;
let openpgpModuleFailure = null;
const OPENPGP_IMPORT_TIMEOUT_MS = 2000;
const OPENPGP_DEBUG_STORAGE_KEY = "forum_debug_signing";

function openPgpDebugEnabled() {
  try {
    const pageFlag = globalThis.document?.querySelector?.("[data-signing-debug-enabled='true']");
    if (pageFlag) {
      return true;
    }
  } catch (_error) {
    // Ignore DOM lookup failures and fall back to local storage.
  }
  try {
    return globalThis.localStorage?.getItem(OPENPGP_DEBUG_STORAGE_KEY) === "1";
  } catch (_error) {
    return false;
  }
}

function logOpenPgpDebug(event, details = {}) {
  if (!openPgpDebugEnabled()) {
    return;
  }
  try {
    console.debug("[openpgp_loader]", event, details);
  } catch (_error) {
    // Ignore console failures in restricted environments.
  }
}

function formatDiagnosticMessage(error) {
  if (!error) {
    return "unknown error";
  }
  if (typeof error.diagnosticMessage === "string" && error.diagnosticMessage) {
    return error.diagnosticMessage;
  }
  if (typeof error.message === "string" && error.message) {
    return error.message;
  }
  return String(error);
}

function classifyOpenPgpError(error) {
  if (error instanceof OpenPgpUnavailableError) {
    return error;
  }
  logOpenPgpDebug("classify_runtime_error", {
    diagnosticMessage: formatDiagnosticMessage(error),
  });
  return new OpenPgpUnavailableError(
    "openpgp_runtime_failed",
    "Browser signing is unavailable because the local signing library failed.",
    formatDiagnosticMessage(error),
  );
}

function describeOpenPgpFailure(error) {
  const classified = classifyOpenPgpError(error);
  switch (classified.code) {
    case "insecure_context":
      return "Browser signing is unavailable on this insecure HTTP page.";
    case "missing_bigint":
      return "Browser signing is unavailable because this browser does not support JavaScript BigInt.";
    case "crypto_unavailable":
      return "Browser signing is unavailable because browser cryptography APIs are missing.";
    case "openpgp_import_failed":
      return "Browser signing is unavailable because the OpenPGP module failed to load.";
    case "openpgp_runtime_failed":
      return "Browser signing is unavailable because the local signing library failed.";
    default:
      return "Browser signing is unavailable.";
  }
}

async function loadOpenPgp() {
  if (openpgpModuleFailure) {
    logOpenPgpDebug("cached_failure", {
      code: openpgpModuleFailure.code,
      diagnosticMessage: formatDiagnosticMessage(openpgpModuleFailure),
    });
    throw openpgpModuleFailure;
  }

  if (typeof BigInt !== "function") {
    logOpenPgpDebug("missing_bigint", {
      bigIntType: typeof BigInt,
    });
    openpgpModuleFailure = new OpenPgpUnavailableError(
      "missing_bigint",
      "Browser signing is unavailable because this browser does not support JavaScript BigInt.",
    );
    throw openpgpModuleFailure;
  }

  if (typeof globalThis.crypto !== "object" || typeof globalThis.crypto.getRandomValues !== "function") {
    logOpenPgpDebug("crypto_unavailable", {
      cryptoType: typeof globalThis.crypto,
      hasGetRandomValues: typeof globalThis.crypto?.getRandomValues === "function",
    });
    openpgpModuleFailure = new OpenPgpUnavailableError(
      "crypto_unavailable",
      "Browser signing is unavailable because browser cryptography APIs are missing.",
    );
    throw openpgpModuleFailure;
  }

  if (globalThis.isSecureContext === false) {
    logOpenPgpDebug("insecure_context", {
      isSecureContext: globalThis.isSecureContext,
      locationHref: globalThis.location?.href || "",
    });
    openpgpModuleFailure = new OpenPgpUnavailableError(
      "insecure_context",
      "Browser signing is unavailable on this insecure HTTP page.",
    );
    throw openpgpModuleFailure;
  }

  if (!openpgpModulePromise) {
    let importPromise;
    const moduleSpecifier = "./vendor/openpgp.min.mjs";
    logOpenPgpDebug("begin_import", {
      moduleSpecifier,
      isSecureContext: globalThis.isSecureContext,
      hasBigInt: typeof BigInt === "function",
      hasCryptoGetRandomValues: typeof globalThis.crypto?.getRandomValues === "function",
      locationHref: globalThis.location?.href || "",
    });
    try {
      const importModule = globalThis.Function(
        "specifier",
        "return import(specifier);",
      );
      importPromise = importModule(moduleSpecifier);
    } catch (error) {
      logOpenPgpDebug("import_setup_failed", {
        moduleSpecifier,
        diagnosticMessage: formatDiagnosticMessage(error),
      });
      openpgpModuleFailure = new OpenPgpUnavailableError(
        "openpgp_import_failed",
        "Browser signing is unavailable because the OpenPGP module failed to load.",
        formatDiagnosticMessage(error),
      );
      throw openpgpModuleFailure;
    }
    const timeoutPromise = new Promise((_, reject) => {
      globalThis.setTimeout(() => {
        logOpenPgpDebug("import_timeout", {
          moduleSpecifier,
          timeoutMs: OPENPGP_IMPORT_TIMEOUT_MS,
        });
        reject(
          new OpenPgpUnavailableError(
            "openpgp_import_failed",
            "Browser signing is unavailable because the OpenPGP module failed to load.",
            "timed out while loading the OpenPGP module",
          ),
        );
      }, OPENPGP_IMPORT_TIMEOUT_MS);
    });
    openpgpModulePromise = Promise.race([importPromise, timeoutPromise]).catch((error) => {
      logOpenPgpDebug("import_failed", {
        moduleSpecifier,
        diagnosticMessage: formatDiagnosticMessage(error),
      });
      openpgpModuleFailure = new OpenPgpUnavailableError(
        "openpgp_import_failed",
        "Browser signing is unavailable because the OpenPGP module failed to load.",
        formatDiagnosticMessage(error),
      );
      throw openpgpModuleFailure;
    });
  }

  try {
    const module = await openpgpModulePromise;
    logOpenPgpDebug("import_succeeded");
    return module;
  } catch (error) {
    throw classifyOpenPgpError(error);
  }
}

export {
  OpenPgpUnavailableError,
  classifyOpenPgpError,
  describeOpenPgpFailure,
  loadOpenPgp,
};
