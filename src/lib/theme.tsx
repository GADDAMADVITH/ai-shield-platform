import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { applyAppearance, loadAppearance } from "@/lib/settings-store";

export type ThemeMode = "dark" | "light";
export type ThemePreference = ThemeMode | "system";

type ThemeContextValue = {
  /** Resolved theme applied to the document */
  theme: ThemeMode;
  /** User preference including system */
  preference: ThemePreference;
  setPreference: (pref: ThemePreference) => void;
  toggle: () => void;
};

const ThemeCtx = createContext<ThemeContextValue>({
  theme: "dark",
  preference: "dark",
  setPreference: () => {},
  toggle: () => {},
});

function systemTheme(): ThemeMode {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function resolveTheme(pref: ThemePreference): ThemeMode {
  return pref === "system" ? systemTheme() : pref;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePreference>("dark");
  const [theme, setTheme] = useState<ThemeMode>("dark");

  useEffect(() => {
    const stored = localStorage.getItem("ais-theme-pref") as ThemePreference | null;
    const legacy = localStorage.getItem("ais-theme") as ThemeMode | null;
    const next =
      stored === "dark" || stored === "light" || stored === "system"
        ? stored
        : legacy === "dark" || legacy === "light"
          ? legacy
          : "dark";
    setPreferenceState(next);
    setTheme(resolveTheme(next));
    applyAppearance(loadAppearance());
  }, []);

  useEffect(() => {
    const resolved = resolveTheme(preference);
    setTheme(resolved);
    const root = document.documentElement;
    if (resolved === "dark") root.classList.add("dark");
    else root.classList.remove("dark");
    try {
      localStorage.setItem("ais-theme-pref", preference);
      localStorage.setItem("ais-theme", resolved);
    } catch {
      /* ignore */
    }
  }, [preference]);

  useEffect(() => {
    if (preference !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: light)");
    const onChange = () => setTheme(systemTheme());
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [preference]);

  return (
    <ThemeCtx.Provider
      value={{
        theme,
        preference,
        setPreference: setPreferenceState,
        toggle: () => setPreferenceState((p) => (resolveTheme(p) === "dark" ? "light" : "dark")),
      }}
    >
      {children}
    </ThemeCtx.Provider>
  );
}

export const useTheme = () => useContext(ThemeCtx);
