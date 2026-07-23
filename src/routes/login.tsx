import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect, type FormEvent } from "react";
import {
  ShieldCheck,
  Lock,
  Radar,
  ScanLine,
  Moon,
  Sun,
} from "lucide-react";
import { toast } from "sonner";
import { Card, Chip } from "@/components/ui-primitives";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { GoogleIcon } from "@/components/google-icon";
import {
  CreateAccountDialog,
  type CreateAccountPayload,
} from "@/components/create-account-dialog";
import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";
import { requireGuest, isAuthenticated } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";
import { messageForApiError } from "@/lib/api/errors";
import { loadAppearance } from "@/lib/settings-store";

export const Route = createFileRoute("/login")({
  beforeLoad: () => {
    requireGuest();
  },
  head: () => ({
    meta: [
      { title: "Sign In · AI Shield" },
      {
        name: "description",
        content: "Sign in to AI Shield — AI Application Security Assessment Platform.",
      },
      { property: "og:title", content: "Sign In · AI Shield" },
      {
        property: "og:description",
        content: "Sign in to AI Shield — AI Application Security Assessment Platform.",
      },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const { theme, toggle } = useTheme();
  const { login, register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) {
      void navigate({ to: loadAppearance().defaultLandingPage, replace: true });
    }
  }, [navigate]);

  function goAfterAuth(to: "/" | "/projects" | "/reports" = "/") {
    void navigate({ to });
  }

  async function signIn(e?: FormEvent) {
    e?.preventDefault();
    const mail = email.trim();
    if (!mail || !password) {
      toast.error("Email and password are required");
      return;
    }
    setSubmitting(true);
    try {
      const user = await login(mail, password, remember);
      toast.success("Signed in", { description: `Welcome back, ${user.name}.` });
      goAfterAuth(loadAppearance().defaultLandingPage);
    } catch (error) {
      toast.error("Sign in failed", { description: messageForApiError(error) });
    } finally {
      setSubmitting(false);
    }
  }

  function continueWithGoogle() {
    toast.message("Google sign-in is not available yet", {
      description: "Use email and password, or create an account.",
    });
  }

  async function handleCreateAccount(payload: CreateAccountPayload) {
    const user = await register(payload.name, payload.email, payload.password);
    toast.success("Account created", { description: `Welcome, ${user.name}.` });
    goAfterAuth("/");
  }

  return (
    <div className="relative flex min-h-screen w-full items-center justify-center grid-noise p-5">
      <div aria-hidden className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 h-[520px] w-[520px] rounded-full bg-info/10 blur-[140px] dark:bg-info/[0.07]" />
        <div className="absolute top-1/3 -right-40 h-[520px] w-[520px] rounded-full bg-accent/10 blur-[140px] dark:bg-white/[0.03]" />
      </div>

      <button
        type="button"
        onClick={toggle}
        aria-label="Toggle theme"
        className="absolute right-5 top-5 z-20 grid h-9 w-9 place-items-center rounded-xl border border-border bg-surface/60 text-muted-foreground backdrop-blur-2xl transition-colors hover:text-foreground"
      >
        {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </button>

      <div className="relative z-10 w-full max-w-[920px] animate-float-in">
        <Card className="overflow-hidden !p-0">
          <div className="grid md:grid-cols-2">
            <div className="relative flex flex-col justify-between border-b border-border bg-elevated/30 p-8 md:border-b-0 md:border-r md:p-10">
              <div>
                <div className="flex items-center gap-2.5">
                  <div className="grid h-10 w-10 place-items-center rounded-xl bg-foreground text-background shadow-soft">
                    <ShieldCheck className="h-5 w-5" strokeWidth={2.25} />
                  </div>
                  <div className="min-w-0">
                    <div className="font-mono text-[13px] font-medium tracking-tight">AI Shield</div>
                    <div className="text-[11px] text-muted-foreground">Enterprise · v2.4</div>
                  </div>
                </div>

                <h1 className="mt-8 text-2xl font-semibold tracking-tight md:text-[1.75rem] md:leading-tight">
                  AI Shield
                </h1>
                <p className="mt-2 max-w-xs text-sm leading-relaxed text-muted-foreground">
                  AI Application Security Assessment Platform
                </p>

                <Chip tone="muted" className="mt-5">
                  <Lock className="h-3 w-3" /> Secure access
                </Chip>
              </div>

              <SecurityGraphic />
            </div>

            <div className="flex flex-col justify-center p-8 md:p-10">
              <div className="mb-1 font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                Authentication
              </div>
              <h2 className="text-lg font-semibold tracking-tight">Sign in to your workspace</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Continue to the AI Shield security console.
              </p>

              <form className="mt-7 space-y-4" onSubmit={(e) => void signIn(e)}>
                <label className="block">
                  <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                    Email
                  </span>
                  <Input
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    className="h-auto rounded-xl border-border bg-surface/60 px-3 py-2.5 text-sm shadow-none focus-visible:border-foreground/40 focus-visible:bg-surface focus-visible:ring-4 focus-visible:ring-foreground/5"
                  />
                </label>

                <label className="block">
                  <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                    Password
                  </span>
                  <Input
                    type="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="h-auto rounded-xl border-border bg-surface/60 px-3 py-2.5 text-sm shadow-none focus-visible:border-foreground/40 focus-visible:bg-surface focus-visible:ring-4 focus-visible:ring-foreground/5"
                  />
                </label>

                <div className="flex items-center justify-between gap-3 pt-0.5">
                  <label className="inline-flex cursor-pointer items-center gap-2 text-sm text-muted-foreground">
                    <Checkbox
                      checked={remember}
                      onCheckedChange={(v) => setRemember(v === true)}
                      className="rounded-md border-border"
                    />
                    Remember me
                  </label>
                  <button
                    type="button"
                    className="font-mono text-[11px] text-muted-foreground transition-colors hover:text-foreground"
                  >
                    Forgot password
                  </button>
                </div>

                <div className="flex flex-col gap-2 pt-2">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-foreground px-4 py-2.5 text-sm font-medium text-background transition-transform hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:scale-100"
                  >
                    <Lock className="h-4 w-4" strokeWidth={2.25} />
                    {submitting ? "Signing in…" : "Sign In"}
                  </button>
                  <button
                    type="button"
                    disabled={submitting}
                    onClick={() => void signIn()}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-border bg-surface/50 px-4 py-2.5 text-sm text-foreground transition-colors hover:bg-hover disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Continue
                  </button>
                </div>
              </form>

              <div className="my-5 flex items-center gap-3">
                <div className="h-px flex-1 bg-border" />
                <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                  Or
                </span>
                <div className="h-px flex-1 bg-border" />
              </div>

              <button
                type="button"
                onClick={continueWithGoogle}
                className="inline-flex w-full items-center justify-center gap-2.5 rounded-2xl border border-border bg-surface/50 px-4 py-2.5 text-sm text-foreground transition-colors hover:bg-hover"
              >
                <GoogleIcon className="h-4 w-4 shrink-0" />
                Continue with Google
              </button>

              <p className="mt-5 text-center text-sm text-muted-foreground">
                Don&apos;t have an account?{" "}
                <button
                  type="button"
                  onClick={() => setRegisterOpen(true)}
                  className="font-medium text-foreground underline-offset-4 transition-colors hover:underline"
                >
                  Create Account
                </button>
              </p>
            </div>
          </div>
        </Card>

        <div className="mt-5 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 font-mono text-[11px] text-muted-foreground">
          <span>v2.4.0</span>
          <span className="text-border">·</span>
          <button type="button" className="transition-colors hover:text-foreground">
            Privacy Policy
          </button>
          <span className="text-border">·</span>
          <button type="button" className="transition-colors hover:text-foreground">
            Terms
          </button>
        </div>
      </div>

      <CreateAccountDialog
        open={registerOpen}
        onOpenChange={setRegisterOpen}
        onCreate={handleCreateAccount}
      />
    </div>
  );
}

function SecurityGraphic() {
  return (
    <div
      aria-hidden
      className="relative mt-10 overflow-hidden rounded-2xl border border-border bg-surface/40 p-5 md:mt-12"
    >
      <div className="absolute inset-0 grid-noise opacity-60" />
      <div className="relative flex items-center justify-between gap-4">
        <div className="grid h-12 w-12 place-items-center rounded-2xl border border-border bg-elevated/80">
          <ShieldCheck className="h-5 w-5 text-foreground" strokeWidth={1.75} />
        </div>
        <div className="h-px flex-1 bg-gradient-to-r from-border via-foreground/25 to-border" />
        <div className="grid h-12 w-12 place-items-center rounded-2xl border border-border bg-elevated/80">
          <Radar className="h-5 w-5 text-muted-foreground" strokeWidth={1.75} />
        </div>
        <div className="h-px flex-1 bg-gradient-to-r from-border via-foreground/25 to-border" />
        <div className="grid h-12 w-12 place-items-center rounded-2xl border border-border bg-elevated/80">
          <ScanLine className="h-5 w-5 text-muted-foreground" strokeWidth={1.75} />
        </div>
      </div>
      <div className="relative mt-4 flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
          Continuous assessment
        </span>
        <span
          className={cn(
            "inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-success",
          )}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-success shadow-[0_0_12px_hsl(142_71%_45%/0.6)]" />
          Online
        </span>
      </div>
      <div className="relative mt-3 h-1.5 overflow-hidden rounded-full bg-hover">
        <div className="h-full w-[72%] rounded-full bg-foreground/70" />
      </div>
    </div>
  );
}
