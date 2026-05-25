export function MainSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-6">
      {/* Question number */}
      <div className="mb-4 h-3 w-[120px] animate-pulse rounded bg-muted" />
      {/* Question body */}
      <div className="mb-5 h-20 w-full animate-pulse rounded-md bg-muted" />
      {/* Answer label */}
      <div className="mb-2.5 h-[11px] w-16 animate-pulse rounded bg-muted" />
      {/* Answer textarea */}
      <div className="mb-4 h-[152px] w-full animate-pulse rounded-md bg-muted" />
      {/* Action row */}
      <div className="flex items-center justify-between">
        <div className="h-3 w-[120px] animate-pulse rounded bg-muted" />
        <div className="flex gap-2">
          <div className="h-8 w-[90px] animate-pulse rounded-md bg-muted" />
          <div className="h-8 w-[110px] animate-pulse rounded-md bg-muted" />
        </div>
      </div>
    </div>
  );
}

export function SidebarSkeleton() {
  return (
    <aside className="sticky top-2 flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
      <div className="mb-1 h-3 w-20 animate-pulse rounded bg-muted" />
      <div className="h-1 w-full animate-pulse rounded-full bg-muted" />
      {[0, 1, 2, 3, 4].map((i) => (
        <div key={i} className="h-7 w-full animate-pulse rounded bg-muted" />
      ))}
    </aside>
  );
}
