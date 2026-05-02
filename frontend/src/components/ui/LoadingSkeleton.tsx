export function TableSkeleton({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div className="animate-pulse">
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 py-3 border-b border-[var(--color-border)]">
          {Array.from({ length: cols }).map((_, c) => (
            <div key={c} className="h-4 bg-[var(--color-border)] rounded flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="animate-pulse bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6">
      <div className="h-4 bg-[var(--color-border)] rounded w-1/3 mb-3" />
      <div className="h-6 bg-[var(--color-border)] rounded w-1/2" />
    </div>
  );
}
