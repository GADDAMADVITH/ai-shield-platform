import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export function Card({ className, children, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...rest}
      className={cn(
        "relative rounded-3xl border border-border bg-card/60 p-6 backdrop-blur-2xl hover-lift",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function SectionHeader({
  eyebrow,
  title,
  action,
}: {
  eyebrow?: string;
  title: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-4 flex items-end justify-between gap-4">
      <div>
        {eyebrow && (
          <div className="mb-1 font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            {eyebrow}
          </div>
        )}
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
      </div>
      {action}
    </div>
  );
}

export function StatusDot({ tone = "success" }: { tone?: "success" | "warning" | "danger" | "info" | "muted" }) {
  const map = {
    success: "bg-success shadow-[0_0_12px_hsl(142_71%_45%/0.6)]",
    warning: "bg-warning shadow-[0_0_12px_hsl(38_92%_50%/0.55)]",
    danger: "bg-destructive shadow-[0_0_12px_hsl(0_84%_60%/0.55)]",
    info: "bg-info shadow-[0_0_12px_hsl(217_91%_60%/0.5)]",
    muted: "bg-muted-foreground/50",
  } as const;
  return <span className={cn("inline-block h-1.5 w-1.5 rounded-full", map[tone])} />;
}

export function Chip({
  children,
  tone = "muted",
  className,
}: {
  children: ReactNode;
  tone?: "muted" | "success" | "warning" | "danger" | "info";
  className?: string;
}) {
  const map = {
    muted: "border-border bg-hover/60 text-muted-foreground",
    success: "border-success/25 bg-success/10 text-success",
    warning: "border-warning/30 bg-warning/10 text-warning",
    danger: "border-destructive/30 bg-destructive/10 text-destructive",
    info: "border-info/30 bg-info/10 text-info",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider",
        map[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function ScoreRing({
  score,
  size = 168,
  strokeWidth = 10,
  label = "Security Score",
}: {
  score: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}) {
  const radius = (size - strokeWidth) / 2;
  const c = 2 * Math.PI * radius;
  const offset = c - (score / 100) * c;
  const grade = score >= 90 ? "A" : score >= 80 ? "A-" : score >= 70 ? "B" : score >= 60 ? "C" : "D";
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          className="text-border"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <defs>
          <linearGradient id="scoreGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--foreground)" stopOpacity="0.95" />
            <stop offset="100%" stopColor="var(--foreground)" stopOpacity="0.4" />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#scoreGrad)"
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 900ms cubic-bezier(0.16,1,0.3,1)" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <div className="font-mono text-4xl font-medium tracking-tight tabular-nums">{score}</div>
        <div className="mt-0.5 flex items-center gap-1.5 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
          <span>{label}</span>
          <span className="rounded-md border border-border bg-elevated px-1 py-0.5 font-mono text-foreground">{grade}</span>
        </div>
      </div>
    </div>
  );
}

export function Sparkline({
  data,
  height = 44,
  className,
  tone = "foreground",
}: {
  data: number[];
  height?: number;
  className?: string;
  tone?: "foreground" | "success" | "danger" | "info";
}) {
  const w = 120;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const pts = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = height - ((v - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    })
    .join(" ");
  const areaPts = `0,${height} ${pts} ${w},${height}`;
  const stroke = tone === "success" ? "var(--success)" : tone === "danger" ? "var(--destructive)" : tone === "info" ? "var(--info)" : "var(--foreground)";
  return (
    <svg viewBox={`0 0 ${w} ${height}`} className={cn("h-11 w-full", className)} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`sp-${tone}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.25" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={areaPts} fill={`url(#sp-${tone})`} />
      <polyline points={pts} fill="none" stroke={stroke} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
