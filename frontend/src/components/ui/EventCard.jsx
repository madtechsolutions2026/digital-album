import { motion } from 'framer-motion';
import { Calendar, Images, Trash2, KeyRound } from 'lucide-react';

const COVER_GRADIENTS = [
  'from-primary-600 via-primary-500 to-gold-400',
  'from-gold-500 via-primary-500 to-primary-700',
  'from-primary-700 via-primary-500 to-gold-300',
  'from-gold-400 via-primary-600 to-primary-900',
];

function formatDate(dateStr) {
  if (!dateStr) return null;
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function EventCard({ event, isSelected, onClick, onDelete }) {
  const gradient = COVER_GRADIENTS[event.event_id % COVER_GRADIENTS.length];
  const initial = event.name?.charAt(0)?.toUpperCase() || '?';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -6 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      onClick={onClick}
      className="relative cursor-pointer group"
    >
      {/* Gradient border wrapper */}
      <div
        className={`
          relative rounded-3xl p-[1.5px] transition-all duration-300
          bg-gradient-to-br
          ${isSelected
            ? `${gradient} shadow-glow-primary`
            : 'from-primary-100 via-primary-100 to-primary-100 group-hover:from-primary-500 group-hover:via-primary-400 group-hover:to-gold-400 group-hover:shadow-glow-primary'
          }
        `}
      >
        <div className="rounded-[calc(1.5rem-1.5px)] bg-white overflow-hidden">
          {/* Cover */}
          <div className={`relative aspect-[4/3] bg-gradient-to-br ${gradient} overflow-hidden`}>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="font-display text-7xl font-extrabold text-white/25 select-none">
                {initial}
              </span>
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/0 to-black/10" />

            {isSelected && (
              <motion.div
                layoutId="eventCardActiveBadge"
                className="absolute top-3 right-3 px-3 py-1 rounded-full bg-white/90 backdrop-blur-sm text-primary-700 text-xs font-bold shadow-soft"
              >
                Selected
              </motion.div>
            )}

            {onDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(event);
                }}
                className="absolute top-3 left-3 p-2 rounded-full bg-black/30 backdrop-blur-sm text-white/80 opacity-0 group-hover:opacity-100 hover:bg-rose-500/90 hover:text-white transition-all duration-200"
                aria-label={`Delete ${event.name}`}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}

            <div className="absolute bottom-0 left-0 right-0 p-4">
              <h4 className="font-display text-white font-bold text-lg leading-tight text-balance drop-shadow-sm">
                {event.name}
              </h4>
            </div>
          </div>

          {/* Meta */}
          <div className="px-4 py-3.5 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-ink/60 text-xs font-medium">
                <Calendar className="w-3.5 h-3.5" />
                <span>{formatDate(event.event_date) || 'No date set'}</span>
              </div>
              <div className="flex items-center gap-1.5 text-ink/60 text-xs font-medium">
                <Images className="w-3.5 h-3.5" />
                <span>{event.photo_count}</span>
              </div>
            </div>
            {event.access_code && (
              <div className="flex items-center gap-1.5 text-primary-600 text-xs font-semibold">
                <KeyRound className="w-3.5 h-3.5" />
                <span className="font-mono tracking-widest">{event.access_code}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
