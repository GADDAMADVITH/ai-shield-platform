import { useEffect, useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  User,
  SlidersHorizontal,
  Palette,
  KeyRound,
  ShieldCheck,
  LogOut,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui-primitives";
import { requireAuth } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";
import { applyAppearance, loadAppearance } from "@/lib/settings-store";
import {
  AccountPanel,
  ApiKeysPanel,
  AppearancePanel,
  PreferencesPanel,
  ProfilePanel,
  SecurityPanel,
} from "@/components/settings/panels";

const sections = [
  { id: "profile", label: "Profile", icon: User },
  { id: "prefs", label: "Preferences", icon: SlidersHorizontal },
  { id: "theme", label: "Appearance", icon: Palette },
  { id: "keys", label: "API Keys", icon: KeyRound },
  { id: "security", label: "Security", icon: ShieldCheck },
  { id: "account", label: "Account", icon: LogOut },
] as const;

type SectionId = (typeof sections)[number]["id"];

function isSectionId(value: unknown): value is SectionId {
  return typeof value === "string" && sections.some((s) => s.id === value);
}

export const Route = createFileRoute("/settings")({
  beforeLoad: () => {
    requireAuth();
  },
  validateSearch: (search: Record<string, unknown>): { section?: SectionId } => {
    return {
      section: isSectionId(search.section) ? search.section : undefined,
    };
  },
  head: () => ({
    meta: [
      { title: "Settings · AI Shield" },
      { name: "description", content: "Manage your AI Shield workspace, security keys, and preferences." },
      { property: "og:title", content: "Settings · AI Shield" },
      { property: "og:description", content: "Manage your AI Shield workspace, security keys, and preferences." },
    ],
  }),
  component: Settings,
});

function Settings() {
  const search = Route.useSearch();
  const [active, setActive] = useState<SectionId>(search.section ?? "profile");
  const navigate = useNavigate();
  const { logout } = useAuth();

  useEffect(() => {
    applyAppearance(loadAppearance());
  }, []);

  useEffect(() => {
    if (search.section) setActive(search.section);
  }, [search.section]);

  function handleLogout() {
    logout();
    void navigate({ to: "/login", replace: true });
  }

  function selectSection(id: SectionId) {
    setActive(id);
    void navigate({
      to: "/settings",
      search: id === "profile" ? {} : { section: id },
      replace: true,
    });
  }

  return (
    <AppShell>
      <div className="mb-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">Workspace</div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
      </div>

      <div className="grid gap-5 lg:grid-cols-[240px_1fr]">
        <Card className="!p-2 h-fit">
          <nav className="space-y-0.5">
            {sections.map((s) => {
              const Icon = s.icon;
              const isActive = active === s.id;
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => selectSection(s.id)}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? "bg-hover text-foreground"
                      : "text-muted-foreground hover:bg-hover/50 hover:text-foreground"
                  }`}
                >
                  <Icon className="h-4 w-4" strokeWidth={1.6} />
                  {s.label}
                </button>
              );
            })}
          </nav>
        </Card>

        <div className="min-w-0">
          {active === "profile" ? <ProfilePanel /> : null}
          {active === "prefs" ? <PreferencesPanel /> : null}
          {active === "theme" ? <AppearancePanel /> : null}
          {active === "keys" ? <ApiKeysPanel /> : null}
          {active === "security" ? <SecurityPanel /> : null}
          {active === "account" ? <AccountPanel onLogout={handleLogout} /> : null}
        </div>
      </div>
    </AppShell>
  );
}
