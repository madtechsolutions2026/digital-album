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
  // Varied heights so the loading state already hints at the masonry layout
  const heights = ['aspect-[3/4]', 'aspect-square', 'aspect-[4/5]', 'aspect-[3/4]'];

  return (
    <div className="columns-2 md:columns-3 lg:columns-4 gap-5 space-y-5">
      {[...Array(8)].map((_, i) => (
        <div key={i} className="break-inside-avoid mb-5">
          <div className={`relative overflow-hidden rounded-3xl bg-primary-100/50 ${heights[i % heights.length]}`}>
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent animate-shimmer" />
          </div>
        </div>
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
