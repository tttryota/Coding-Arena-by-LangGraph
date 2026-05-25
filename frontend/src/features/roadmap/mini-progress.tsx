import { scoreLevel } from "@/lib/score";

interface MiniProgressProps {
  value: number;
  width?: number;
}

export function MiniProgress({ value, width = 64 }: MiniProgressProps) {
  const lvl = scoreLevel(value);
  return (
    <div
      className="h-1 overflow-hidden rounded-full bg-muted"
      style={{ width }}
    >
      <div
        className="h-full rounded-full transition-[width] duration-150 ease-out"
        style={{
          width: `${value || 0}%`,
          backgroundColor: lvl.fg,
        }}
      />
    </div>
  );
}
