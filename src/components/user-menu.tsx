import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";
import {
  User,
  Building2,
  Settings,
  KeyRound,
  BookOpen,
  LifeBuoy,
  LogOut,
  ChevronDown,
  ExternalLink,
  Mail,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Chip } from "@/components/ui-primitives";
import { ConfirmDialog, PrimaryButton, SecondaryButton, SettingsField, SettingsInput } from "@/components/settings/shared";
import { useAuth } from "@/lib/auth-context";
import { useProjects } from "@/lib/projects";
import { loadReports } from "@/lib/reports-store";
import { useWorkspace } from "@/lib/workspace-context";

function userInitials(name?: string | null) {
  return (name ?? "A")
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function loadProfileExtra() {
  if (typeof window === "undefined") {
    return { organization: "AI Shield Labs", jobTitle: "Administrator" };
  }
  try {
    const raw = localStorage.getItem("ais-profile-extra");
    if (!raw) return { organization: "AI Shield Labs", jobTitle: "Administrator" };
    const parsed = JSON.parse(raw) as { organization?: string; jobTitle?: string };
    return {
      organization: parsed.organization?.trim() || "AI Shield Labs",
      jobTitle: parsed.jobTitle?.trim() || "Administrator",
    };
  } catch {
    return { organization: "AI Shield Labs", jobTitle: "Administrator" };
  }
}

function saveProfileExtra(organization: string, jobTitle: string) {
  try {
    localStorage.setItem("ais-profile-extra", JSON.stringify({ organization, jobTitle }));
  } catch {
    /* ignore */
  }
}

type UserMenuProps = {
  variant?: "navbar" | "sidebar";
};

export function UserMenu({ variant = "navbar" }: UserMenuProps) {
  const navigate = useNavigate();
  const { user, logout, updateUser } = useAuth();
  const { projects } = useProjects();
  const { current: workspace } = useWorkspace();

  const [profileOpen, setProfileOpen] = useState(false);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const [docsOpen, setDocsOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [logoutOpen, setLogoutOpen] = useState(false);

  const initials = userInitials(user?.name);
  const extra = useMemo(() => loadProfileExtra(), [profileOpen, user]);

  const workspaceStats = useMemo(() => {
    const reports = typeof window !== "undefined" ? loadReports().length : 0;
    const scans = projects.reduce((sum, p) => sum + (p.scans || 0), 0);
    return {
      name: workspace.name,
      slug: workspace.slug,
      projects: projects.length,
      reports,
      scans,
    };
  }, [projects, workspace, workspaceOpen]);

  function goSettings(section?: "profile" | "keys") {
    void navigate({
      to: "/settings",
      search: section ? { section } : {},
    });
  }

  function confirmLogout() {
    setLogoutOpen(false);
    void logout().then(() => {
      void navigate({ to: "/login", replace: true });
    });
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          {variant === "sidebar" ? (
            <button
              type="button"
              className="flex w-full items-center gap-3 rounded-2xl border border-border bg-elevated/50 p-3 text-left transition-colors hover:bg-hover/50"
            >
              <div className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-foreground/90 to-foreground/60 font-mono text-xs text-background">
                {initials}
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-[13px] font-medium">{user?.name ?? "User"}</div>
                <div className="truncate text-[11px] text-muted-foreground">{user?.email ?? ""}</div>
              </div>
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            </button>
          ) : (
            <button
              type="button"
              aria-label="User menu"
              className="inline-flex items-center gap-2 rounded-xl bg-hover/40 py-1 pl-1 pr-2 text-muted-foreground transition-colors hover:text-foreground"
            >
              <span className="grid h-7 w-7 place-items-center rounded-full bg-gradient-to-br from-foreground/90 to-foreground/60 font-mono text-[10px] text-background">
                {initials}
              </span>
              <span className="hidden max-w-[96px] truncate text-sm text-foreground sm:inline">
                {user?.name ?? "User"}
              </span>
              <ChevronDown className="hidden h-3.5 w-3.5 sm:block" />
            </button>
          )}
        </DropdownMenuTrigger>

        <DropdownMenuContent
          align="end"
          sideOffset={10}
          className="w-[280px] rounded-2xl border-border bg-card/95 p-1.5 shadow-glass backdrop-blur-2xl"
        >
          <div className="px-2.5 py-2.5">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-foreground/90 to-foreground/60 font-mono text-xs text-background">
                {initials}
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{user?.name ?? "User"}</div>
                <div className="truncate text-[11px] text-muted-foreground">{user?.email ?? ""}</div>
                <Chip tone="muted" className="mt-1.5">
                  {user?.role ?? "Member"}
                </Chip>
              </div>
            </div>
          </div>

          <DropdownMenuSeparator className="bg-border" />

          <DropdownMenuItem
            className="cursor-pointer rounded-xl px-2.5 py-2 focus:bg-hover"
            onSelect={() => setProfileOpen(true)}
          >
            <User className="h-4 w-4" strokeWidth={1.75} /> Profile
          </DropdownMenuItem>
          <DropdownMenuItem
            className="cursor-pointer rounded-xl px-2.5 py-2 focus:bg-hover"
            onSelect={() => setWorkspaceOpen(true)}
          >
            <Building2 className="h-4 w-4" strokeWidth={1.75} /> Workspace
          </DropdownMenuItem>
          <DropdownMenuItem
            className="cursor-pointer rounded-xl px-2.5 py-2 focus:bg-hover"
            onSelect={() => goSettings()}
          >
            <Settings className="h-4 w-4" strokeWidth={1.75} /> Settings
          </DropdownMenuItem>
          <DropdownMenuItem
            className="cursor-pointer rounded-xl px-2.5 py-2 focus:bg-hover"
            onSelect={() => goSettings("keys")}
          >
            <KeyRound className="h-4 w-4" strokeWidth={1.75} /> API Keys
          </DropdownMenuItem>

          <DropdownMenuSeparator className="bg-border" />

          <DropdownMenuItem
            className="cursor-pointer rounded-xl px-2.5 py-2 focus:bg-hover"
            onSelect={() => setDocsOpen(true)}
          >
            <BookOpen className="h-4 w-4" strokeWidth={1.75} /> Documentation
          </DropdownMenuItem>
          <DropdownMenuItem
            className="cursor-pointer rounded-xl px-2.5 py-2 focus:bg-hover"
            onSelect={() => setHelpOpen(true)}
          >
            <LifeBuoy className="h-4 w-4" strokeWidth={1.75} /> Help & Support
          </DropdownMenuItem>

          <DropdownMenuSeparator className="bg-border" />

          <DropdownMenuItem
            className="cursor-pointer rounded-xl px-2.5 py-2 text-destructive focus:bg-hover focus:text-destructive"
            onSelect={() => setLogoutOpen(true)}
          >
            <LogOut className="h-4 w-4" strokeWidth={1.75} /> Logout
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <ProfileDialog
        open={profileOpen}
        onOpenChange={setProfileOpen}
        initials={initials}
        name={user?.name ?? ""}
        email={user?.email ?? ""}
        role={user?.role ?? ""}
        organization={extra.organization}
        jobTitle={extra.jobTitle || user?.role || "Administrator"}
        onSave={(next) => {
          updateUser({
            name: next.name,
            email: next.email,
            role: next.jobTitle || next.role,
          });
          saveProfileExtra(next.organization, next.jobTitle);
          toast.success("Profile updated", { description: "Mock profile changes applied." });
          setProfileOpen(false);
        }}
      />

      <Dialog open={workspaceOpen} onOpenChange={setWorkspaceOpen}>
        <DialogContent className="max-w-md gap-0 overflow-hidden rounded-3xl border-border bg-card/95 p-0 shadow-glass backdrop-blur-2xl sm:rounded-3xl">
          <DialogHeader className="space-y-1 border-b border-border px-6 py-5 text-left">
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
              Workspace
            </div>
            <DialogTitle className="text-lg font-semibold tracking-tight">{workspaceStats.name}</DialogTitle>
            <DialogDescription className="text-sm text-muted-foreground">
              Enterprise workspace overview (mock).
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-3 p-6">
            {[
              { k: "Workspace Name", v: workspaceStats.name },
              { k: "Workspace ID", v: workspaceStats.slug },
              { k: "Projects Count", v: String(workspaceStats.projects) },
              { k: "Reports Count", v: String(workspaceStats.reports) },
              { k: "Scans Completed", v: String(workspaceStats.scans) },
            ].map((row) => (
              <div key={row.k} className="rounded-2xl border border-border bg-surface/40 px-4 py-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                  {row.k}
                </div>
                <div className="mt-1 text-sm">{row.v}</div>
              </div>
            ))}
          </div>
          <DialogFooter className="border-t border-border px-6 py-4 sm:justify-end">
            <SecondaryButton onClick={() => setWorkspaceOpen(false)}>Close</SecondaryButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={docsOpen} onOpenChange={setDocsOpen}>
        <DialogContent className="max-w-md gap-0 overflow-hidden rounded-3xl border-border bg-card/95 p-0 shadow-glass backdrop-blur-2xl sm:rounded-3xl">
          <DialogHeader className="space-y-1 border-b border-border px-6 py-5 text-left">
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
              Documentation
            </div>
            <DialogTitle className="text-lg font-semibold tracking-tight">AI Shield Docs</DialogTitle>
            <DialogDescription className="text-sm text-muted-foreground">
              Mock documentation placeholder for product guides and API references.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 p-6 text-sm text-muted-foreground">
            <p>Browse getting-started guides, scan profiles, and remediation playbooks.</p>
            <ul className="space-y-2">
              {["Quickstart", "Scan Configuration", "Findings Taxonomy", "API Reference"].map((item) => (
                <li
                  key={item}
                  className="flex items-center justify-between rounded-2xl border border-border bg-surface/40 px-4 py-3 text-foreground"
                >
                  <span>{item}</span>
                  <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
                </li>
              ))}
            </ul>
          </div>
          <DialogFooter className="border-t border-border px-6 py-4 sm:justify-end">
            <SecondaryButton
              onClick={() => {
                toast.success("Documentation link opened (mock)");
                setDocsOpen(false);
              }}
            >
              Open Docs
            </SecondaryButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={helpOpen} onOpenChange={setHelpOpen}>
        <DialogContent className="max-w-md gap-0 overflow-hidden rounded-3xl border-border bg-card/95 p-0 shadow-glass backdrop-blur-2xl sm:rounded-3xl">
          <DialogHeader className="space-y-1 border-b border-border px-6 py-5 text-left">
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
              Help & Support
            </div>
            <DialogTitle className="text-lg font-semibold tracking-tight">Get assistance</DialogTitle>
            <DialogDescription className="text-sm text-muted-foreground">
              Contact support or review product documentation.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 p-6">
            {[
              { k: "Support Email", v: "support@aishield.co", icon: Mail },
              { k: "Documentation", v: "docs.aishield.co", icon: BookOpen },
              { k: "Version", v: "Enterprise · v2.4", icon: Building2 },
            ].map((row) => {
              const Icon = row.icon;
              return (
                <div
                  key={row.k}
                  className="flex items-center gap-3 rounded-2xl border border-border bg-surface/40 px-4 py-3"
                >
                  <Icon className="h-4 w-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
                  <div className="min-w-0">
                    <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                      {row.k}
                    </div>
                    <div className="mt-0.5 text-sm">{row.v}</div>
                  </div>
                </div>
              );
            })}
          </div>
          <DialogFooter className="border-t border-border px-6 py-4 sm:justify-end">
            <SecondaryButton onClick={() => setHelpOpen(false)}>Close</SecondaryButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={logoutOpen}
        onOpenChange={setLogoutOpen}
        title="Log out of AI Shield?"
        description="You will need to sign in again to access the workspace."
        confirmLabel="Logout"
        onConfirm={confirmLogout}
      />
    </>
  );
}

function ProfileDialog({
  open,
  onOpenChange,
  initials,
  name,
  email,
  role,
  organization,
  jobTitle,
  onSave,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initials: string;
  name: string;
  email: string;
  role: string;
  organization: string;
  jobTitle: string;
  onSave: (next: {
    name: string;
    email: string;
    role: string;
    organization: string;
    jobTitle: string;
  }) => void;
}) {
  const [draftName, setDraftName] = useState(name);
  const [draftEmail, setDraftEmail] = useState(email);
  const [draftOrg, setDraftOrg] = useState(organization);
  const [draftTitle, setDraftTitle] = useState(jobTitle);

  useEffect(() => {
    if (!open) return;
    setDraftName(name);
    setDraftEmail(email);
    setDraftOrg(organization);
    setDraftTitle(jobTitle);
  }, [open, name, email, organization, jobTitle]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg gap-0 overflow-hidden rounded-3xl border-border bg-card/95 p-0 shadow-glass backdrop-blur-2xl sm:rounded-3xl">
        <DialogHeader className="space-y-1 border-b border-border px-6 py-5 text-left">
          <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Profile
          </div>
          <DialogTitle className="text-lg font-semibold tracking-tight">Your identity</DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            Mock edit — changes persist in local session only.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 p-6">
          <div className="flex items-center gap-3">
            <div className="grid h-14 w-14 place-items-center rounded-full bg-gradient-to-br from-foreground/90 to-foreground/60 font-mono text-sm text-background">
              {initials}
            </div>
            <div>
              <div className="text-sm font-medium">{draftName || name}</div>
              <div className="text-[12px] text-muted-foreground">{draftEmail || email}</div>
              <Chip tone="muted" className="mt-1.5">
                {role}
              </Chip>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <SettingsField label="Name">
              <SettingsInput value={draftName} onChange={(e) => setDraftName(e.target.value)} />
            </SettingsField>
            <SettingsField label="Email">
              <SettingsInput
                type="email"
                value={draftEmail}
                onChange={(e) => setDraftEmail(e.target.value)}
              />
            </SettingsField>
            <SettingsField label="Organization">
              <SettingsInput value={draftOrg} onChange={(e) => setDraftOrg(e.target.value)} />
            </SettingsField>
            <SettingsField label="Job Title">
              <SettingsInput value={draftTitle} onChange={(e) => setDraftTitle(e.target.value)} />
            </SettingsField>
            <SettingsField label="Role">
              <SettingsInput value={role} readOnly className="opacity-70" />
            </SettingsField>
            <SettingsField label="Member Since">
              <SettingsInput value="Aug 12, 2025" readOnly className="opacity-70" />
            </SettingsField>
          </div>
        </div>

        <DialogFooter className="gap-2 border-t border-border px-6 py-4 sm:space-x-0">
          <SecondaryButton onClick={() => onOpenChange(false)}>Cancel</SecondaryButton>
          <PrimaryButton
            onClick={() =>
              onSave({
                name: draftName.trim() || name,
                email: draftEmail.trim() || email,
                role,
                organization: draftOrg.trim() || organization,
                jobTitle: draftTitle.trim() || jobTitle,
              })
            }
          >
            Save Changes
          </PrimaryButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
