import { scoreLevel } from "@/lib/score";

interface ScoreBadgeProps {
  score: number | null | undefined;
  variant?: "label" | "numeral";
}

export function ScoreBadge({ score, variant = "label" }: ScoreBadgeProps) {
  const lvl = scoreLevel(score);

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium leading-snug"
      style={{ color: lvl.fg, backgroundColor: lvl.bg }}
    >
      {variant === "numeral" ? (
        <span className="font-mono font-semibold tabular-nums">
          {score == null || score === 0 ? "—" : score}
        </span>
      ) : (
        lvl.label
      )}
    </span>
  );
}
