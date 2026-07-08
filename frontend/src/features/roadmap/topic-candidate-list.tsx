import { cn } from "@/lib/utils";
import type { TopicCandidate, TopicSource } from "@/types/api";

function SourceBadge({ source }: { source: TopicSource }) {
  const config: Record<TopicSource, { label: string; cls: string }> = {
    preset: {
      label: "プリセット",
      cls: "border-blue-500/25 bg-blue-500/10 text-blue-400",
    },
    manual: {
      label: "手動",
      cls: "border-slate-500/30 bg-slate-500/[0.12] text-muted-foreground",
    },
  };
  const c = config[source];

  return (
    <span
      className={cn(
        "inline-flex items-center whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px] font-medium leading-snug",
        c.cls,
      )}
    >
      {c.label}
    </span>
  );
}

interface TopicCandidateListProps {
  candidates: TopicCandidate[];
  selected: string | null;
  onSelect: (name: string) => void;
}

export function TopicCandidateList({
  candidates,
  selected,
  onSelect,
}: TopicCandidateListProps) {
  return (
    <div
      className="flex max-h-[220px] flex-col overflow-y-auto rounded-md border border-border bg-background"
      role="listbox"
      aria-label="トピック候補"
    >
      {candidates.map((c) => {
        const isSelected = selected === c.name;
        return (
          <button
            key={c.name}
            type="button"
            role="option"
            aria-selected={isSelected}
            onClick={() => onSelect(c.name)}
            className={cn(
              "flex items-center gap-3 border-b border-border px-3 py-2.5 text-left transition-colors duration-100 last:border-b-0",
              isSelected
                ? "bg-[rgb(37_99_235/0.18)] shadow-[inset_2px_0_0_0_var(--color-primary)]"
                : "hover:bg-[rgb(51_65_85/0.4)]",
            )}
          >
            {/* Radio indicator */}
            <span
              className={cn(
                "flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-[1.5px] transition-colors duration-100",
                isSelected
                  ? "border-primary bg-primary"
                  : "border-muted-foreground bg-background",
              )}
            >
              {isSelected && (
                <span className="h-1.5 w-1.5 rounded-full bg-white" />
              )}
            </span>

            {/* Name */}
            <span
              className={cn(
                "min-w-0 flex-1 text-sm font-medium tracking-tight",
                isSelected ? "text-blue-100" : "text-foreground",
              )}
            >
              {c.name}
            </span>

            {/* Source badge */}
            <SourceBadge source={c.source} />
          </button>
        );
      })}
    </div>
  );
}
