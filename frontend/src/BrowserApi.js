const FALLBACK_HASH = "#/";
const LANGUAGE_KEY = "superlig.language";

export const readHash = () => {
  if (typeof window === "undefined") {
    return FALLBACK_HASH;
  }

  return window.location.hash || FALLBACK_HASH;
};

export const writeHash = hash => {
  if (typeof window === "undefined") {
    return;
  }

  if (window.location.hash === hash) {
    return;
  }

  window.location.hash = hash;
};

export const subscribeToHashChange = callback => {
  if (typeof window === "undefined") {
    return () => {};
  }

  const handler = () => callback(readHash());
  window.addEventListener("hashchange", handler);

  return () => window.removeEventListener("hashchange", handler);
};

export const readStoredLanguage = () => {
  if (typeof window === "undefined") {
    return "";
  }

  try {
    return window.localStorage.getItem(LANGUAGE_KEY) ?? "";
  } catch (_error) {
    return "";
  }
};

export const writeStoredLanguage = value => {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(LANGUAGE_KEY, value);
  } catch (_error) {
    // Ignore storage failures in private browsing / restricted environments.
  }
};

export const scrollToId = id => {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return;
  }

  const node = document.getElementById(id);
  if (!node) {
    return;
  }

  node.scrollIntoView({ behavior: "smooth", block: "start" });
};
