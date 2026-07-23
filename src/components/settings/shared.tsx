import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export const fieldInputClass =
  "w-full rounded-xl border border-border bg-surface/60 px-3 py-2.5 text-sm outline-none transition-all focus:border-foreground/40 focus:bg-surface focus:ring-4 focus:ring-foreground/5";

export const selectTriggerClass =
  "h-auto w-full rounded-xl border-border bg-surface/60 px-3 py-2.5 text-sm shadow-none focus:ring-4 focus:ring-foreground/5";

export const selectContentClass =
  "z-[60] rounded-2xl border-border bg-popover/95 backdrop-blur-2xl";

export function SettingsField({
  label,
  children,
  className,
}: {
  label: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <label className={cn("block", className)}>
      <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </span>
      {children}
    </label>
  );
}

export function SettingsInput(props: React.ComponentProps<"input">) {
  return <input {...props} className={cn(fieldInputClass, props.className)} />;
}

export function ToggleRow({
  title,
  description,
  checked,
  onCheckedChange,
}: {
  title: string;
  description?: string;
  checked: boolean;
  onCheckedChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-border bg-surface/40 px-4 py-3">
      <div className="min-w-0">
        <div className="text-sm">{title}</div>
        {description ? (
          <div className="mt-0.5 text-[11px] text-muted-foreground">{description}</div>
        ) : null}
      </div>
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
    </div>
  );
}

export function SettingsSelect({
  label,
  value,
  onValueChange,
  options,
}: {
  label: string;
  value: string;
  onValueChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <SettingsField label={label}>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger className={selectTriggerClass}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent className={selectContentClass}>
          {options.map((o) => (
            <SelectItem key={o.value} value={o.value} className="rounded-xl">
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </SettingsField>
  );
}

export function PrimaryButton({
  children,
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl bg-foreground px-3 py-2 text-sm font-medium text-background transition-transform hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function SecondaryButton({
  children,
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Confirm",
  destructive,
  onConfirm,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel?: string;
  destructive?: boolean;
  onConfirm: () => void;
}) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="rounded-3xl border-border bg-card/95 shadow-glass backdrop-blur-2xl sm:rounded-3xl">
        <AlertDialogHeader>
          <AlertDialogTitle className="tracking-tight">{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="gap-2 sm:space-x-0">
          <AlertDialogCancel className="rounded-xl border-border bg-surface/50">
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            className={cn(
              "rounded-xl",
              destructive
                ? "bg-destructive text-destructive-foreground hover:bg-destructive/90"
                : "bg-foreground text-background hover:bg-foreground/90",
            )}
            onClick={onConfirm}
          >
            {confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
