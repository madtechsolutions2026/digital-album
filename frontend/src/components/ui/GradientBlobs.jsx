/**
 * Ambient floating gradient blobs, used as a page backdrop. Purely
 * decorative - absolutely positioned, pointer-events disabled, sits
 * behind content via negative z-index.
 */
export default function GradientBlobs({ variant = 'default' }) {
  if (variant === 'hero') {
    return (
      <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute -top-32 -left-24 w-[32rem] h-[32rem] bg-primary-500/30 rounded-full blur-3xl animate-blob" />
        <div className="absolute top-1/3 -right-24 w-[28rem] h-[28rem] bg-gold-500/25 rounded-full blur-3xl animate-blob" style={{ animationDelay: '4s' }} />
        <div className="absolute -bottom-40 left-1/3 w-[30rem] h-[30rem] bg-primary-400/20 rounded-full blur-3xl animate-blob" style={{ animationDelay: '8s' }} />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-200/40 rounded-full blur-3xl animate-blob" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-gold-200/40 rounded-full blur-3xl animate-blob" style={{ animationDelay: '5s' }} />
    </div>
  );
}
