import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  suffix?: string;
  hint?: string;
  valueColor?: string;
  onClick?: () => void;
  hot?: boolean;
}

export function StatCard({
  icon: Icon,
  label,
  value,
  suffix,
  hint,
  valueColor,
  onClick,
  hot,
}: StatCardProps) {
  const Tag = onClick ? "button" : "div";
  return (
    <Tag
      type={onClick ? "button" : undefined}
      className={[
        "relative flex flex-col rounded-lg border border-border bg-card px-5 py-[18px] text-left transition-[background,border-color] duration-150 ease-out",
        onClick && "cursor-pointer hover:bg-[rgb(51_65_85/0.25)]",
        onClick &&
          "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
        hot && "border-[rgb(37_99_235/0.55)] hover:border-[rgb(59_130_246/0.8)]",
      ]
        .filter(Boolean)
        .join(" ")}
      onClick={onClick}
    >
      {/* Header: label + icon */}
      <div className="mb-3 flex items-start justify-between gap-2">
        <span className="text-xs leading-[1.4] text-muted-foreground">
          {label}
        </span>
        <span className="relative inline-flex">
          <Icon size={14} className="text-muted-foreground" />
          {hot && (
            <span
              className="absolute -right-[5px] -top-[3px] h-1.5 w-1.5 rounded-full bg-primary"
              style={{ boxShadow: "0 0 0 2px var(--card)" }}
              aria-label="未読あり"
            />
          )}
        </span>
      </div>

      {/* Value */}
      <div
        className="font-mono text-[28px] font-semibold leading-none tracking-[-0.02em] tabular-nums"
        style={{ color: valueColor }}
      >
        <span>{value}</span>
        {suffix && (
          <span className="ml-1 text-[13px] font-medium tracking-normal text-muted-foreground">
            {suffix}
          </span>
        )}
      </div>

      {/* Hint */}
      {hint && (
        <div className="mt-2.5 text-[11px] leading-[1.4] text-muted-foreground">
          {hint}
        </div>
      )}
    </Tag>
  );
}
