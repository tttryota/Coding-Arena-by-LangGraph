import { Skeleton } from "@/components/ui/skeleton";

export function FeedbackSkeletonCard() {
  return (
    <div className="flex flex-col gap-2.5 rounded-lg border border-border bg-card px-5 py-[18px]">
      <div className="flex items-start gap-2.5">
        <span className="w-2 shrink-0" />
        <div className="flex min-w-0 flex-1 flex-col gap-1.5">
          <Skeleton className="h-4 w-[60%]" />
          <Skeleton className="h-3 w-[40%]" />
        </div>
        <Skeleton className="h-3 w-[60px]" />
      </div>
      <div className="pl-[18px]">
        <Skeleton className="h-3 w-[90%] mt-1.5" />
        <Skeleton className="h-3 w-[75%] mt-2" />
      </div>
    </div>
  );
}
