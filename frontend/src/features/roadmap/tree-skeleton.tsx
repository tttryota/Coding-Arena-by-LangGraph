import { Skeleton } from "@/components/ui/skeleton";

function SkeletonRow({
  indent = 0,
  textWidth = "40%",
}: {
  indent?: 0 | 1 | 2;
  textWidth?: string;
}) {
  const pl = indent === 2 ? "pl-16" : indent === 1 ? "pl-[38px]" : "";
  return (
    <div className={`flex items-center gap-2.5 px-2.5 py-2.5 ${pl}`}>
      <Skeleton className="h-3.5 w-3.5 rounded" />
      <Skeleton className="h-4 w-4 rounded" />
      <Skeleton className="h-[13px] rounded" style={{ width: textWidth }} />
      <div className="flex-1" />
      <Skeleton className="h-1.5 w-16 rounded-full" />
      <Skeleton className="h-[18px] w-[38px] rounded-full" />
    </div>
  );
}

export function TreeSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-2">
      <div className="p-2">
        <SkeletonRow indent={0} textWidth="220px" />
        <SkeletonRow indent={1} textWidth="160px" />
        <SkeletonRow indent={2} textWidth="240px" />
        <SkeletonRow indent={2} textWidth="200px" />
        <SkeletonRow indent={2} textWidth="180px" />
        <SkeletonRow indent={1} textWidth="180px" />
        <SkeletonRow indent={0} textWidth="200px" />
        <SkeletonRow indent={1} textWidth="160px" />
      </div>
    </div>
  );
}
