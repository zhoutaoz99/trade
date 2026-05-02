export function TableSkeleton({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div className="animate-pulse">
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 py-3 border-b border-[#2a2e3f]">
          {Array.from({ length: cols }).map((_, c) => (
            <div key={c} className="h-4 bg-[#2a2e3f] rounded flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="animate-pulse bg-[#1a1d2e] border border-[#2a2e3f] rounded-xl p-6">
      <div className="h-4 bg-[#2a2e3f] rounded w-1/3 mb-3" />
      <div className="h-6 bg-[#2a2e3f] rounded w-1/2" />
    </div>
  );
}
