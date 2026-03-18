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
    throw openpgpModuleFailure;
  }

  if (typeof BigInt !== "function") {
    openpgpModuleFailure = new OpenPgpUnavailableError(
      "missing_bigint",
      "Browser signing is unavailable because this browser does not support JavaScript BigInt.",
    );
    throw openpgpModuleFailure;
  }

  if (typeof globalThis.crypto !== "object" || typeof globalThis.crypto.getRandomValues !== "function") {
    openpgpModuleFailure = new OpenPgpUnavailableError(
      "crypto_unavailable",
      "Browser signing is unavailable because browser cryptography APIs are missing.",
    );
    throw openpgpModuleFailure;
  }

  if (globalThis.isSecureContext === false) {
    openpgpModuleFailure = new OpenPgpUnavailableError(
      "insecure_context",
      "Browser signing is unavailable on this insecure HTTP page.",
    );
    throw openpgpModuleFailure;
  }

  if (!openpgpModulePromise) {
    let importPromise;
    try {
      const importModule = globalThis.Function(
        "specifier",
        "return import(specifier);",
      );
      importPromise = importModule("./vendor/openpgp.min.mjs");
    } catch (error) {
      openpgpModuleFailure = new OpenPgpUnavailableError(
        "openpgp_import_failed",
        "Browser signing is unavailable because the OpenPGP module failed to load.",
        formatDiagnosticMessage(error),
      );
      throw openpgpModuleFailure;
    }
    const timeoutPromise = new Promise((_, reject) => {
      globalThis.setTimeout(() => {
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
      openpgpModuleFailure = new OpenPgpUnavailableError(
        "openpgp_import_failed",
        "Browser signing is unavailable because the OpenPGP module failed to load.",
        formatDiagnosticMessage(error),
      );
      throw openpgpModuleFailure;
    });
  }

  try {
    return await openpgpModulePromise;
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
