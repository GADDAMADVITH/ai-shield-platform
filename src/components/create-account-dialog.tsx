import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { messageForApiError } from "@/lib/api/errors";

const fieldClass =
  "h-auto w-full rounded-xl border-border bg-surface/60 px-3 py-2.5 text-sm shadow-none focus-visible:border-foreground/40 focus-visible:bg-surface focus-visible:ring-4 focus-visible:ring-foreground/5";

export type CreateAccountPayload = {
  name: string;
  email: string;
  password: string;
};

type CreateAccountDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreate: (payload: CreateAccountPayload) => void | Promise<void>;
};

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function CreateAccountDialog({ open, onOpenChange, onCreate }: CreateAccountDialogProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    setName("");
    setEmail("");
    setPassword("");
    setConfirm("");
    setError(null);
    setSubmitting(false);
  }, [open]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const fullName = name.trim();
    const mail = email.trim();

    if (!fullName || !mail || !password || !confirm) {
      setError("All fields are required.");
      return;
    }
    if (!isValidEmail(mail)) {
      setError("Enter a valid email address.");
      return;
    }
    if (password.length < 8 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
      setError("Password must be 8+ characters with at least one letter and one number.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    setError(null);
    setSubmitting(true);
    try {
      await onCreate({ name: fullName, email: mail, password });
      onOpenChange(false);
    } catch (err) {
      setError(messageForApiError(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md gap-0 overflow-hidden rounded-3xl border-border bg-card/95 p-0 shadow-glass backdrop-blur-2xl sm:rounded-3xl">
        <form onSubmit={handleSubmit}>
          <DialogHeader className="space-y-1 border-b border-border px-6 py-5 text-left">
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
              Registration
            </div>
            <DialogTitle className="text-lg font-semibold tracking-tight">Create Account</DialogTitle>
            <DialogDescription className="text-sm text-muted-foreground">
              Create your AI Shield account to manage projects and connections.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 px-6 py-5">
            <Field label="Full Name">
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
                placeholder="Advith"
                className={fieldClass}
              />
            </Field>
            <Field label="Email">
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                placeholder="you@company.com"
                className={fieldClass}
              />
            </Field>
            <Field label="Password">
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                className={fieldClass}
              />
            </Field>
            <Field label="Confirm Password">
              <Input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                autoComplete="new-password"
                className={fieldClass}
              />
            </Field>

            {error ? (
              <p className="rounded-xl border border-destructive/30 bg-destructive/10 px-3 py-2 text-[12.5px] text-destructive">
                {error}
              </p>
            ) : null}
          </div>

          <DialogFooter className="gap-2 border-t border-border px-6 py-4 sm:space-x-0">
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              className="inline-flex items-center justify-center rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-foreground transition-colors hover:bg-hover"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center justify-center rounded-xl bg-foreground px-3 py-2 text-sm font-medium text-background transition-transform hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
            >
              {submitting ? "Creating…" : "Create Account"}
            </button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </span>
      {children}
    </label>
  );
}
