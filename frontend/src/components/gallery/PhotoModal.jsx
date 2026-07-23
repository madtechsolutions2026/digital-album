import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState, useCallback } from 'react';
import {
  X, ChevronLeft, ChevronRight, Download, Share2, Heart,
  Calendar, Maximize2, Check
} from 'lucide-react';

function formatDate(dateStr) {
  if (!dateStr) return null;
  return new Date(dateStr).toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function PhotoModal({ photos, index, onClose, onNavigate }) {
  const [liked, setLiked] = useState(false);
  const [copied, setCopied] = useState(false);

  const photo = photos[index];
  const hasPrev = index > 0;
  const hasNext = index < photos.length - 1;

  const goPrev = useCallback(() => hasPrev && onNavigate(index - 1), [hasPrev, index, onNavigate]);
  const goNext = useCallback(() => hasNext && onNavigate(index + 1), [hasNext, index, onNavigate]);

  useEffect(() => {
    setLiked(false);
    setCopied(false);
  }, [index]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft') goPrev();
      if (e.key === 'ArrowRight') goNext();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, goPrev, goNext]);

  if (!photo) return null;

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({ url: photo.file_path, title: 'Wedding photo' });
        return;
      } catch {
        // user cancelled or share failed - fall through to clipboard copy
      }
    }
    try {
      await navigator.clipboard.writeText(photo.file_path);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable - nothing more we can do here
    }
  };

  const dims = photo.photo_metadata?.stored_size;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-ink/90 backdrop-blur-xl"
      onClick={onClose}
    >
      {/* Close */}
      <button
        onClick={onClose}
        className="absolute top-5 right-5 z-10 p-2.5 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
      >
        <X className="w-5 h-5" />
      </button>

      {/* Counter */}
      <div className="absolute top-5 left-5 z-10 px-3.5 py-1.5 rounded-full bg-white/10 backdrop-blur-md text-white/90 text-sm font-medium">
        {index + 1} / {photos.length}
      </div>

      {/* Prev / Next */}
      {hasPrev && (
        <button
          onClick={(e) => { e.stopPropagation(); goPrev(); }}
          className="absolute left-4 md:left-6 top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
      )}
      {hasNext && (
        <button
          onClick={(e) => { e.stopPropagation(); goNext(); }}
          className="absolute right-4 md:right-6 top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      )}

      <div
        className="relative w-full max-w-5xl max-h-[85vh] flex flex-col items-center"
        onClick={(e) => e.stopPropagation()}
      >
        <AnimatePresence mode="wait">
          <motion.img
            key={photo.photo_id}
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.97 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            src={photo.file_path}
            alt="Wedding photo"
            className="max-w-full max-h-[70vh] rounded-2xl shadow-soft-xl object-contain"
          />
        </AnimatePresence>

        {/* Toolbar */}
        <div className="mt-5 w-full max-w-md glass-dark rounded-2xl px-5 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3 text-white/80 text-xs">
            {photo.uploaded_at && (
              <span className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5" />
                {formatDate(photo.uploaded_at)}
              </span>
            )}
            {dims && (
              <span className="hidden sm:flex items-center gap-1.5">
                <Maximize2 className="w-3.5 h-3.5" />
                {dims.width}×{dims.height}
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setLiked((v) => !v)}
              className={`p-2 rounded-full transition-colors ${
                liked ? 'bg-rose-500 text-white' : 'bg-white/10 hover:bg-white/20 text-white'
              }`}
            >
              <Heart className={`w-4 h-4 ${liked ? 'fill-current' : ''}`} />
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={handleShare}
              className="p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Share2 className="w-4 h-4" />}
            </motion.button>
            <motion.a
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              href={photo.file_path}
              download
              className="p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
            >
              <Download className="w-4 h-4" />
            </motion.a>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
