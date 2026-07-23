import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Check,
  Copy,
  KeyRound,
  Monitor,
  Moon,
  Sun,
  Trash2,
  Plus,
  Download,
  LogOut,
  ShieldCheck,
  Smartphone,
} from "lucide-react";
import { Card, Chip, SectionHeader } from "@/components/ui-primitives";
import { useAuth } from "@/lib/auth-context";
import { useTheme, type ThemePreference } from "@/lib/theme";
import {
  applyAppearance,
  loadApiKeys,
  loadAppearance,
  loadWorkspacePrefs,
  maskKey,
  saveApiKeys,
  saveAppearance,
  saveWorkspacePrefs,
  type AppearanceSettings,
  type DefaultLandingPage,
  type DisplayDensity,
  type MockApiKey,
  type WorkspacePreferences,
} from "@/lib/settings-store";
import { pushNotification } from "@/lib/notifications-store";
import { useWorkspace } from "@/lib/workspace-context";
import {
  ConfirmDialog,
  PrimaryButton,
  SecondaryButton,
  SettingsField,
  SettingsInput,
  SettingsSelect,
  ToggleRow,
} from "@/components/settings/shared";

export function ProfilePanel() {
  const { user, updateUser } = useAuth();
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [organization, setOrganization] = useState("AI Shield Labs");
  const [jobTitle, setJobTitle] = useState(user?.role ?? "Administrator");

  useEffect(() => {
    setName(user?.name ?? "");
    setEmail(user?.email ?? "");
    setJobTitle(user?.role ?? "Administrator");
  }, [user]);

  function save() {
    updateUser({
      name: name.trim() || user?.name || "User",
      email: email.trim() || user?.email || "",
      role: jobTitle.trim() || user?.role || "Administrator",
    });
    try {
      localStorage.setItem(
        "ais-profile-extra",
        JSON.stringify({ organization, jobTitle }),
      );
    } catch {
      /* ignore */
    }
    toast.success("Profile saved", { description: "Mock profile changes applied." });
    pushNotification({
      title: "Settings Updated",
      description: "Profile settings updated successfully.",
      category: "system",
      severity: "success",
    });
  }

  function cancel() {
    setName(user?.name ?? "");
    setEmail(user?.email ?? "");
    setOrganization("AI Shield Labs");
    setJobTitle(user?.role ?? "Administrator");
    toast.message("Changes discarded");
  }

  return (
    <Card>
      <SectionHeader eyebrow="Profile" title="Your identity" />
      <div className="grid gap-4 md:grid-cols-2">
        <SettingsField label="Name">
          <SettingsInput value={name} onChange={(e) => setName(e.target.value)} />
        </SettingsField>
        <SettingsField label="Email">
          <SettingsInput type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </SettingsField>
        <SettingsField label="Organization">
          <SettingsInput value={organization} onChange={(e) => setOrganization(e.target.value)} />
        </SettingsField>
        <SettingsField label="Job Title">
          <SettingsInput value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />
        </SettingsField>
      </div>
      <div className="mt-5 flex flex-wrap gap-2">
        <PrimaryButton onClick={save}>Save Changes</PrimaryButton>
        <SecondaryButton onClick={cancel}>Cancel</SecondaryButton>
      </div>
    </Card>
  );
}

export function PreferencesPanel() {
  const [prefs, setPrefs] = useState<WorkspacePreferences>(() => loadWorkspacePrefs());

  function update<K extends keyof WorkspacePreferences>(key: K, value: WorkspacePreferences[K]) {
    setPrefs((prev) => {
      const next = { ...prev, [key]: value };
      saveWorkspacePrefs(next);
      return next;
    });
  }

  return (
    <Card>
      <SectionHeader eyebrow="Preferences" title="Workspace defaults" />
      <div className="grid gap-4 md:grid-cols-2">
        <SettingsSelect
          label="Default Scan Profile"
          value={prefs.defaultScanProfile}
          onValueChange={(v) => {
            update("defaultScanProfile", v);
            toast.success("Default scan profile updated");
          }}
          options={[
            { value: "Quick Scan", label: "Quick Scan" },
            { value: "Standard Scan", label: "Standard Scan" },
            { value: "Full Security Assessment", label: "Full Security Assessment" },
          ]}
        />
        <SettingsSelect
          label="Default Environment"
          value={prefs.defaultEnvironment}
          onValueChange={(v) => {
            update("defaultEnvironment", v);
            toast.success("Default environment updated");
          }}
          options={[
            { value: "Development", label: "Development" },
            { value: "Staging", label: "Staging" },
            { value: "Production", label: "Production" },
          ]}
        />
      </div>
      <div className="mt-4 space-y-2">
        <ToggleRow
          title="Enable Notifications"
          description="In-app alerts for critical findings and scan events."
          checked={prefs.notifications}
          onCheckedChange={(v) => {
            update("notifications", v);
            toast.success(v ? "Notifications enabled" : "Notifications disabled");
          }}
        />
        <ToggleRow
          title="Enable Scan Completion Emails"
          description="Email a summary when assessments finish."
          checked={prefs.scanEmails}
          onCheckedChange={(v) => {
            update("scanEmails", v);
            toast.success(v ? "Scan emails enabled" : "Scan emails disabled");
          }}
        />
        <ToggleRow
          title="Auto-save Reports"
          description="Persist report drafts automatically after each scan."
          checked={prefs.autoSaveReports}
          onCheckedChange={(v) => {
            update("autoSaveReports", v);
            toast.success(v ? "Auto-save enabled" : "Auto-save disabled");
          }}
        />
      </div>
    </Card>
  );
}

export function AppearancePanel() {
  const { theme, preference, setPreference } = useTheme();
  const [appearance, setAppearance] = useState<AppearanceSettings>(() => loadAppearance());

  useEffect(() => {
    applyAppearance(appearance);
  }, [appearance]);

  function patch(partial: Partial<AppearanceSettings>) {
    setAppearance((prev) => {
      const next = { ...prev, ...partial };
      saveAppearance(next);
      return next;
    });
  }

  const themes: { id: ThemePreference; label: string; icon: typeof Moon; preview: string }[] = [
    { id: "dark", label: "Dark", icon: Moon, preview: "linear-gradient(135deg, #141414, #202020)" },
    { id: "light", label: "Light", icon: Sun, preview: "linear-gradient(135deg, #ffffff, #f2f2f3)" },
    { id: "system", label: "System", icon: Monitor, preview: "linear-gradient(135deg, #141414 50%, #ffffff 50%)" },
  ];

  const densities: { id: DisplayDensity; label: string; description: string }[] = [
    { id: "comfortable", label: "Comfortable", description: "Standard spacing for everyday work." },
    { id: "compact", label: "Compact", description: "Denser layout for high-volume scanning." },
  ];

  return (
    <div className="space-y-5">
      <Card>
        <SectionHeader
          eyebrow="Appearance"
          title="Theme"
          action={<Chip tone="muted">{preference === "system" ? `System · ${theme}` : preference}</Chip>}
        />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {themes.map((t) => {
            const Icon = t.icon;
            const active = preference === t.id;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => {
                  setPreference(t.id);
                  toast.success(`Theme set to ${t.label}`);
                }}
                className={`group relative overflow-hidden rounded-2xl border p-4 text-left transition-all ${
                  active ? "border-foreground/40 bg-hover/50" : "border-border bg-surface/40 hover:bg-hover/40"
                }`}
              >
                <div
                  className="mb-3 h-24 w-full rounded-xl border border-border"
                  style={{ background: t.preview }}
                />
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-2 text-sm capitalize">
                    <Icon className="h-3.5 w-3.5" /> {t.label}
                  </span>
                  {active ? <Check className="h-4 w-4 text-foreground" /> : null}
                </div>
              </button>
            );
          })}
        </div>
      </Card>

      <Card>
        <SectionHeader eyebrow="Appearance" title="Display density" />
        <div className="grid gap-3 sm:grid-cols-2">
          {densities.map((d) => {
            const active = appearance.density === d.id;
            return (
              <button
                key={d.id}
                type="button"
                onClick={() => {
                  patch({ density: d.id });
                  toast.success(`Density set to ${d.label}`);
                }}
                className={`rounded-2xl border p-4 text-left transition-all ${
                  active ? "border-foreground/40 bg-hover/50" : "border-border bg-surface/40 hover:bg-hover/40"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm">{d.label}</span>
                  {active ? <Check className="h-4 w-4 text-foreground" /> : null}
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">{d.description}</p>
              </button>
            );
          })}
        </div>
      </Card>

      <Card>
        <SectionHeader eyebrow="Appearance" title="Motion" />
        <ToggleRow
          title="Enable UI Animations"
          description="Motion for cards, transitions, and progress indicators."
          checked={appearance.animations}
          onCheckedChange={(v) => {
            patch({ animations: v });
            toast.success(v ? "UI animations enabled" : "UI animations disabled");
          }}
        />
      </Card>

      <Card>
        <SectionHeader eyebrow="Appearance" title="Default landing page" />
        <SettingsSelect
          label="After sign-in"
          value={appearance.defaultLandingPage}
          onValueChange={(v) => {
            patch({ defaultLandingPage: v as DefaultLandingPage });
            toast.success("Default landing page updated");
          }}
          options={[
            { value: "/", label: "Dashboard" },
            { value: "/projects", label: "Projects" },
            { value: "/reports", label: "Reports" },
          ]}
        />
      </Card>
    </div>
  );
}

export function ApiKeysPanel() {
  const [keys, setKeys] = useState<MockApiKey[]>(() => loadApiKeys());
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [revokeId, setRevokeId] = useState<string | null>(null);

  function persist(next: MockApiKey[]) {
    setKeys(next);
    saveApiKeys(next);
  }

  function generate() {
    const id = `key_${Date.now().toString(36)}`;
    const key = `sk_live_${Math.random().toString(36).slice(2, 10)}${Math.random().toString(36).slice(2, 6)}`;
    const next = [
      {
        id,
        name: `key-${keys.length + 1}`,
        key,
        created: "Just now",
        lastUsed: "Never",
      },
      ...keys,
    ];
    persist(next);
    toast.success("API key generated", { description: maskKey(key) });
  }

  async function copy(k: MockApiKey) {
    try {
      await navigator.clipboard.writeText(k.key);
    } catch {
      /* ignore */
    }
    setCopiedId(k.id);
    toast.success("API key copied");
    window.setTimeout(() => setCopiedId(null), 1200);
  }

  function revoke() {
    if (!revokeId) return;
    persist(keys.filter((k) => k.id !== revokeId));
    toast.success("API key revoked");
    setRevokeId(null);
  }

  return (
    <Card>
      <SectionHeader
        eyebrow="API"
        title="Keys"
        action={<Chip tone="info">{keys.length} active</Chip>}
      />
      <div className="mb-4">
        <PrimaryButton onClick={generate}>
          <Plus className="h-4 w-4" strokeWidth={2.25} /> Generate API Key
        </PrimaryButton>
      </div>
      <div className="space-y-2">
        {keys.map((k) => (
          <div
            key={k.id}
            className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-surface/40 p-4"
          >
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-sm">
                <KeyRound className="h-3.5 w-3.5 text-muted-foreground" />
                {k.name}
              </div>
              <div className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                {maskKey(k.key)} · created {k.created} · last used {k.lastUsed}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <SecondaryButton onClick={() => void copy(k)} className="font-mono text-[11px]">
                {copiedId === k.id ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
                {copiedId === k.id ? "Copied" : "Copy"}
              </SecondaryButton>
              <SecondaryButton onClick={() => setRevokeId(k.id)} className="text-destructive hover:text-destructive">
                <Trash2 className="h-3.5 w-3.5" /> Revoke
              </SecondaryButton>
            </div>
          </div>
        ))}
        {keys.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border px-4 py-8 text-center text-sm text-muted-foreground">
            No API keys yet. Generate one to get started.
          </div>
        ) : null}
      </div>

      <ConfirmDialog
        open={!!revokeId}
        onOpenChange={(open) => !open && setRevokeId(null)}
        title="Revoke API key?"
        description="This key will stop working immediately. This mock action cannot be undone."
        confirmLabel="Revoke Key"
        destructive
        onConfirm={revoke}
      />
    </Card>
  );
}

export function SecurityPanel() {
  const [twoFactor, setTwoFactor] = useState(false);
  const [sessions, setSessions] = useState([
    { id: "s1", device: "Chrome · Linux", location: "Hyderabad, IN", current: true, last: "Active now" },
    { id: "s2", device: "Safari · iPhone", location: "Hyderabad, IN", current: false, last: "2 days ago" },
    { id: "s3", device: "Firefox · macOS", location: "Bengaluru, IN", current: false, last: "Last week" },
  ]);
  const [terminateId, setTerminateId] = useState<string | null>(null);

  const activity = [
    { when: "Today · 09:14", detail: "Successful login · Chrome · Linux" },
    { when: "Yesterday · 18:02", detail: "Password challenge passed" },
    { when: "Mar 18 · 11:40", detail: "New session · Safari · iPhone" },
  ];

  return (
    <div className="space-y-5">
      <Card>
        <SectionHeader eyebrow="Security" title="Password" />
        <div className="grid gap-4 md:grid-cols-2">
          <SettingsField label="Current Password">
            <SettingsInput type="password" defaultValue="••••••••" />
          </SettingsField>
          <SettingsField label="New Password">
            <SettingsInput type="password" placeholder="Enter a new password" />
          </SettingsField>
        </div>
        <div className="mt-4">
          <PrimaryButton
            onClick={() => toast.success("Password updated", { description: "Mock password change applied." })}
          >
            Update Password
          </PrimaryButton>
        </div>
      </Card>

      <Card>
        <SectionHeader
          eyebrow="Security"
          title="Two-factor authentication"
          action={<Chip tone={twoFactor ? "success" : "muted"}>{twoFactor ? "Enabled" : "Disabled"}</Chip>}
        />
        <p className="mb-4 text-sm text-muted-foreground">
          Add an authenticator app challenge for sensitive account actions.
        </p>
        <PrimaryButton
          onClick={() => {
            setTwoFactor((v) => !v);
            toast.success(!twoFactor ? "2FA enabled (mock)" : "2FA disabled (mock)");
          }}
        >
          <Smartphone className="h-4 w-4" />
          {twoFactor ? "Disable 2FA" : "Enable 2FA"}
        </PrimaryButton>
      </Card>

      <Card>
        <SectionHeader eyebrow="Security" title="Login sessions" />
        <div className="space-y-2">
          {sessions.map((s) => (
            <div
              key={s.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-surface/40 px-4 py-3"
            >
              <div>
                <div className="flex items-center gap-2 text-sm">
                  {s.device}
                  {s.current ? <Chip tone="success">Current</Chip> : null}
                </div>
                <div className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                  {s.location} · {s.last}
                </div>
              </div>
              {!s.current ? (
                <SecondaryButton onClick={() => setTerminateId(s.id)}>Terminate Session</SecondaryButton>
              ) : null}
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <SectionHeader eyebrow="Security" title="Recent login activity" />
        <ul className="space-y-2">
          {activity.map((a) => (
            <li
              key={a.when}
              className="flex items-start gap-3 rounded-2xl border border-border bg-surface/40 px-4 py-3"
            >
              <ShieldCheck className="mt-0.5 h-4 w-4 text-muted-foreground" strokeWidth={1.6} />
              <div>
                <div className="text-sm">{a.detail}</div>
                <div className="mt-0.5 font-mono text-[11px] text-muted-foreground">{a.when}</div>
              </div>
            </li>
          ))}
        </ul>
      </Card>

      <ConfirmDialog
        open={!!terminateId}
        onOpenChange={(open) => !open && setTerminateId(null)}
        title="Terminate session?"
        description="This device will be signed out immediately. This is a mock action."
        confirmLabel="Terminate"
        destructive
        onConfirm={() => {
          setSessions((prev) => prev.filter((s) => s.id !== terminateId));
          setTerminateId(null);
          toast.success("Session terminated");
        }}
      />
    </div>
  );
}

export function AccountPanel({ onLogout }: { onLogout: () => void }) {
  const { user } = useAuth();
  const { current: workspace } = useWorkspace();
  const [logoutOpen, setLogoutOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  return (
    <div className="space-y-5">
      <Card>
        <SectionHeader eyebrow="Account" title="Workspace membership" />
        <div className="grid gap-3 sm:grid-cols-2">
          {[
            { k: "Account Type", v: "Business" },
            { k: "Workspace", v: workspace.name },
            { k: "Subscription", v: "Enterprise · Active" },
            { k: "Member Since", v: "Aug 12, 2025" },
            { k: "Owner", v: user?.name ?? "—" },
            { k: "Role", v: user?.role ?? "—" },
          ].map((row) => (
            <div key={row.k} className="rounded-2xl border border-border bg-surface/40 px-4 py-3">
              <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">{row.k}</div>
              <div className="mt-1 text-sm">{row.v}</div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <SectionHeader eyebrow="Account" title="Actions" />
        <div className="flex flex-wrap gap-2">
          <SecondaryButton
            onClick={() =>
              toast.success("Export started", {
                description: "Mock account data package is ready.",
              })
            }
          >
            <Download className="h-4 w-4" /> Export Account Data
          </SecondaryButton>
          <SecondaryButton onClick={() => setLogoutOpen(true)}>
            <LogOut className="h-4 w-4" /> Logout
          </SecondaryButton>
          <SecondaryButton
            onClick={() => setDeleteOpen(true)}
            className="border-destructive/30 text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" /> Delete Account
          </SecondaryButton>
        </div>
      </Card>

      <ConfirmDialog
        open={logoutOpen}
        onOpenChange={setLogoutOpen}
        title="Log out of AI Shield?"
        description="You will need to sign in again to access the workspace."
        confirmLabel="Logout"
        onConfirm={() => {
          setLogoutOpen(false);
          onLogout();
        }}
      />

      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete account?"
        description="This mock action permanently removes your workspace access. This cannot be undone."
        confirmLabel="Delete Account"
        destructive
        onConfirm={() => {
          setDeleteOpen(false);
          toast.success("Account deleted (mock)");
          onLogout();
        }}
      />
    </div>
  );
}
