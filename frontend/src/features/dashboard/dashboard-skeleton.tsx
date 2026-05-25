import { Skeleton } from "@/components/ui/skeleton";

export function StatSkeleton() {
  return (
    <div className="flex flex-col rounded-lg border border-border bg-card px-5 py-[18px]">
      <div className="mb-3 flex items-start justify-between">
        <Skeleton className="h-3 w-[90px]" />
        <Skeleton className="h-3.5 w-3.5 rounded-[3px]" />
      </div>
      <Skeleton className="mt-1 h-7 w-14" />
      <Skeleton className="mt-3 h-[11px] w-[110px]" />
    </div>
  );
}

export function RoadmapSectionSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-border bg-card">
      <div className="border-b border-border px-[18px] py-3.5">
        <Skeleton className="h-3.5 w-[120px]" />
      </div>
      <div className="flex flex-col gap-0.5 p-1.5">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 px-3 py-2.5">
            <Skeleton
              className="h-[13px]"
              style={{ width: `${50 + (i % 3) * 12}%` }}
            />
            <Skeleton className="h-1.5 flex-1 rounded-full" />
            <Skeleton className="h-[13px] w-7" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function ActivitySectionSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-border bg-card">
      <div className="border-b border-border px-[18px] py-3.5">
        <Skeleton className="h-3.5 w-[140px]" />
      </div>
      <div className="flex flex-col gap-0.5 p-1.5">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-start gap-3 px-3 py-[11px]">
            <Skeleton className="h-[22px] w-[22px] shrink-0 rounded-[6px]" />
            <div className="flex flex-1 flex-col gap-1">
              <Skeleton
                className="h-[13px]"
                style={{ width: `${45 + (i % 4) * 10}%` }}
              />
              <div className="flex items-center gap-2">
                <Skeleton className="h-[11px] w-10 rounded-full" />
                <Skeleton className="h-[11px] w-12" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
