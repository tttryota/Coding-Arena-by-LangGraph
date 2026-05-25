import { Skeleton } from "@/components/ui/skeleton";

export function SkeletonCard() {
  return (
    <div className="flex flex-col rounded-lg border border-border bg-card p-5">
      <div className="mb-3.5 flex items-start justify-between gap-3">
        <Skeleton className="h-[18px] w-3/5" />
        <Skeleton className="h-[22px] w-14 rounded-full" />
      </div>
      <div className="mb-4 flex items-center gap-3.5">
        <Skeleton className="h-[22px] w-9" />
        <Skeleton className="h-2 flex-1 rounded-full" />
      </div>
      <Skeleton className="mt-4 h-3 w-[70%]" />
      <Skeleton className="mt-[18px] h-[11px] w-[40%]" />
    </div>
  );
}
