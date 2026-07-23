export type DisplayDensity = "comfortable" | "compact";

export type DefaultLandingPage = "/" | "/projects" | "/reports";

export type AppearanceSettings = {
  density: DisplayDensity;
  animations: boolean;
  defaultLandingPage: DefaultLandingPage;
};

export type WorkspacePreferences = {
  defaultScanProfile: string;
  defaultEnvironment: string;
  notifications: boolean;
  scanEmails: boolean;
  autoSaveReports: boolean;
};

const APPEARANCE_KEY = "ais-appearance";
const PREFS_KEY = "ais-workspace-prefs";
const API_KEYS_KEY = "ais-api-keys";

export const DEFAULT_APPEARANCE: AppearanceSettings = {
  density: "comfortable",
  animations: true,
  defaultLandingPage: "/",
};

export const DEFAULT_PREFS: WorkspacePreferences = {
  defaultScanProfile: "Standard Scan",
  defaultEnvironment: "Production",
  notifications: true,
  scanEmails: true,
  autoSaveReports: false,
};

export type MockApiKey = {
  id: string;
  name: string;
  key: string;
  created: string;
  lastUsed: string;
};

export const DEFAULT_API_KEYS: MockApiKey[] = [
  { id: "key_1", name: "production", key: "sk_live_9f2a7ec1d4b8", created: "Aug 2025", lastUsed: "2h ago" },
  { id: "key_2", name: "staging", key: "sk_test_1c8842be90af", created: "Oct 2025", lastUsed: "Yesterday" },
];

function readJson<T extends object>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return { ...fallback, ...(JSON.parse(raw) as Partial<T>) };
  } catch {
    return fallback;
  }
}

function writeJson(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* ignore */
  }
}

function normalizeAppearance(raw: Record<string, unknown>): AppearanceSettings {
  const density: DisplayDensity =
    raw.density === "compact" || raw.density === "comfortable"
      ? raw.density
      : raw.compact === true
        ? "compact"
        : "comfortable";

  const defaultLandingPage: DefaultLandingPage =
    raw.defaultLandingPage === "/projects" || raw.defaultLandingPage === "/reports"
      ? raw.defaultLandingPage
      : "/";

  return {
    density,
    animations: raw.animations !== false,
    defaultLandingPage,
  };
}

export function loadAppearance(): AppearanceSettings {
  if (typeof window === "undefined") return DEFAULT_APPEARANCE;
  try {
    const raw = localStorage.getItem(APPEARANCE_KEY);
    if (!raw) return DEFAULT_APPEARANCE;
    return normalizeAppearance(JSON.parse(raw) as Record<string, unknown>);
  } catch {
    return DEFAULT_APPEARANCE;
  }
}

export function saveAppearance(settings: AppearanceSettings) {
  writeJson(APPEARANCE_KEY, settings);
  applyAppearance(settings);
}

export function applyAppearance(settings: AppearanceSettings) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.removeAttribute("data-accent");
  root.dataset.density = settings.density;
  root.dataset.compact = settings.density === "compact" ? "true" : "false";
  root.dataset.animations = settings.animations ? "on" : "off";
  if (!settings.animations) root.classList.add("reduce-motion");
  else root.classList.remove("reduce-motion");
}

export function loadWorkspacePrefs(): WorkspacePreferences {
  return readJson(PREFS_KEY, DEFAULT_PREFS);
}

export function saveWorkspacePrefs(prefs: WorkspacePreferences) {
  writeJson(PREFS_KEY, prefs);
}

export function loadApiKeys(): MockApiKey[] {
  if (typeof window === "undefined") return DEFAULT_API_KEYS;
  try {
    const raw = localStorage.getItem(API_KEYS_KEY);
    if (!raw) return DEFAULT_API_KEYS;
    const parsed = JSON.parse(raw) as MockApiKey[];
    return Array.isArray(parsed) ? parsed : DEFAULT_API_KEYS;
  } catch {
    return DEFAULT_API_KEYS;
  }
}

export function saveApiKeys(keys: MockApiKey[]) {
  writeJson(API_KEYS_KEY, keys);
}

export function maskKey(key: string) {
  if (key.length <= 10) return key;
  return `${key.slice(0, 8)}··${key.slice(-4)}`;
}
