import { useEffect, useState, type ReactNode } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useAuth } from "@/lib/auth-context";

/** Client-side session gate for AppShell pages (covers full-page refresh). */
export function AuthGate({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const { user, isAuthenticated, refresh } = useAuth();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!isAuthenticated || !user) {
      void navigate({ to: "/login", replace: true });
      return;
    }
    setReady(true);
  }, [isAuthenticated, user, navigate]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
          Checking session…
        </div>
      </div>
    );
  }

  return children;
}
