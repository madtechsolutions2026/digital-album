export default function Skeleton({ className = '', variant = 'default' }) {
  const variants = {
    default: 'h-4 w-full',
    circle: 'rounded-full',
    card: 'h-48 w-full',
    text: 'h-4 w-3/4',
  };

  return (
    <div 
      className={`
        animate-pulse bg-slate-200 dark:bg-slate-700 rounded-lg
        ${variants[variant]}
        ${className}
      `}
    >
      <div className="h-full w-full bg-gradient-to-r from-transparent via-slate-300/50 dark:via-slate-600/50 to-transparent animate-shimmer" />
    </div>
  );
}

export function GallerySkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {[...Array(8)].map((_, i) => (
        <Skeleton key={i} variant="card" className="aspect-square" />
      ))}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="glass-card p-6 space-y-4">
      <Skeleton className="h-6 w-1/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
}
