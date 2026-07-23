import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutGrid,
  FolderKanban,
  ScanLine,
  FileText,
  History,
  Settings,
  Search,
  Sun,
  Moon,
  ShieldCheck,
  Command,
  Plus,
  Menu,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useScanWorkflow } from "@/components/scan-workflow-provider";
import { AuthGate } from "@/components/auth-gate";
import { NotificationCenter } from "@/components/notification-center";
import { UserMenu } from "@/components/user-menu";
import { WorkspaceSelector } from "@/components/workspace-selector";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutGrid },
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/scan", label: "New Scan", icon: ScanLine },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/history", label: "Scan History", icon: History },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

function NavLinks({
  pathname,
  onNavigate,
  className,
}: {
  pathname: string;
  onNavigate?: () => void;
  className?: string;
}) {
  return (
    <nav className={cn("flex flex-col gap-0.5", className)}>
      {nav.map((item) => {
        const active = item.to === "/" ? pathname === "/" : pathname.startsWith(item.to);
        const Icon = item.icon;
        return (
          <Link
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={cn(
              "group relative flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all",
              active
                ? "bg-hover text-foreground"
                : "text-muted-foreground hover:bg-hover/60 hover:text-foreground",
            )}
          >
            {active && (
              <span className="absolute left-0 top-1/2 h-5 w-[2px] -translate-x-2 -translate-y-1/2 rounded-full bg-foreground shadow-[0_0_10px_rgba(255,255,255,0.6)]" />
            )}
            <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
            <span className="truncate">{item.label}</span>
            {item.to === "/scan" && (
              <span className="ml-auto rounded-md bg-elevated px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                ⌘N
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { theme, toggle } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { openStartScan } = useScanWorkflow();

  return (
    <AuthGate>
    <div className="relative min-h-screen w-full grid-noise">
      {/* Ambient orbs */}
      <div aria-hidden className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 h-[520px] w-[520px] rounded-full bg-info/10 blur-[140px] dark:bg-info/[0.07]" />
        <div className="absolute top-1/3 -right-40 h-[520px] w-[520px] rounded-full bg-accent/10 blur-[140px] dark:bg-white/[0.03]" />
      </div>

      <div className="relative mx-auto flex min-h-screen max-w-[1600px] gap-5 p-5">
        {/* Sidebar — desktop */}
        <aside className="sticky top-5 hidden h-[calc(100vh-2.5rem)] w-64 shrink-0 flex-col rounded-3xl border border-border bg-sidebar/70 p-4 backdrop-blur-2xl lg:flex">
          <Link to="/" className="flex items-center gap-2.5 px-2 py-2">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-foreground text-background shadow-soft">
              <ShieldCheck className="h-4.5 w-4.5" strokeWidth={2.25} />
            </div>
            <div className="min-w-0">
              <div className="font-mono text-[13px] font-medium tracking-tight">AI Shield</div>
              <div className="text-[11px] text-muted-foreground">Enterprise · v2.4</div>
            </div>
          </Link>

          <div className="mx-2 my-3 h-px bg-border" />

          <div className="px-2 pb-2 text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
            Workspace
          </div>
          <NavLinks pathname={pathname} />

          <div className="mt-auto space-y-2">
            <UserMenu variant="sidebar" />

            <button
              onClick={toggle}
              className="flex w-full items-center justify-between rounded-xl border border-border bg-surface/40 px-3 py-2 text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              <span className="inline-flex items-center gap-2">
                {theme === "dark" ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
                <span className="font-mono">{theme === "dark" ? "Dark" : "Light"}</span>
              </span>
              <span className="font-mono text-[10px]">Toggle</span>
            </button>
          </div>
        </aside>

        {/* Main */}
        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {/* Topbar */}
          <header className="sticky top-5 z-20 flex items-center gap-3 rounded-2xl border border-border bg-surface/60 px-3 py-2 backdrop-blur-2xl">
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetTrigger asChild>
                <button
                  type="button"
                  aria-label="Open navigation"
                  className="grid h-9 w-9 place-items-center rounded-xl bg-hover/40 text-muted-foreground transition-colors hover:text-foreground lg:hidden"
                >
                  <Menu className="h-4 w-4" />
                </button>
              </SheetTrigger>
              <SheetContent side="left" className="w-[280px] border-border bg-sidebar/95 p-4 backdrop-blur-2xl">
                <SheetHeader className="mb-4 space-y-0 text-left">
                  <SheetTitle className="flex items-center gap-2.5 font-mono text-[13px] font-medium tracking-tight">
                    <span className="grid h-9 w-9 place-items-center rounded-xl bg-foreground text-background shadow-soft">
                      <ShieldCheck className="h-4.5 w-4.5" strokeWidth={2.25} />
                    </span>
                    AI Shield
                  </SheetTitle>
                </SheetHeader>
                <div className="pb-2 text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
                  Workspace
                </div>
                <NavLinks pathname={pathname} onNavigate={() => setMobileOpen(false)} />
              </SheetContent>
            </Sheet>

            <WorkspaceSelector />

            <div className="flex flex-1 items-center gap-2 rounded-xl bg-hover/40 px-3 py-1.5">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                placeholder="Search projects, scans, vulnerabilities…"
                className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              />
              <span className="hidden md:inline-flex items-center gap-1 rounded-md border border-border bg-surface px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                <Command className="h-3 w-3" /> K
              </span>
            </div>

            <button
              type="button"
              onClick={() => openStartScan()}
              className="hidden md:inline-flex items-center gap-2 rounded-xl bg-foreground px-3 py-1.5 text-sm font-medium text-background transition-transform hover:scale-[1.02]"
            >
              <Plus className="h-4 w-4" strokeWidth={2.25} />
              New Scan
            </button>

            <NotificationCenter />

            <button
              type="button"
              onClick={toggle}
              className="grid h-9 w-9 place-items-center rounded-xl bg-hover/40 text-muted-foreground transition-colors hover:text-foreground"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>

            <UserMenu variant="navbar" />
          </header>

          <main className="min-w-0 flex-1 pb-10">{children}</main>
        </div>
      </div>
    </div>
    </AuthGate>
  );
}
