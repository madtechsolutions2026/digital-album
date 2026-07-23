import { motion } from 'framer-motion';
import { useState } from 'react';
import { Heart, Download, ZoomIn, Calendar } from 'lucide-react';

function formatDate(dateStr) {
  if (!dateStr) return null;
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function MasonryGrid({ photos, onPhotoClick }) {
  return (
    <div className="columns-2 md:columns-3 lg:columns-4 gap-5 space-y-5">
      {photos.map((photo, index) => (
        <PhotoCard
          key={photo.photo_id}
          photo={photo}
          index={index}
          onClick={() => onPhotoClick(photo)}
        />
      ))}
    </div>
  );
}

function PhotoCard({ photo, index, onClick }) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isLiked, setIsLiked] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index * 0.04, 0.6), duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="break-inside-avoid mb-5"
    >
      <motion.div
        whileHover={{ y: -4 }}
        transition={{ duration: 0.25 }}
        className={`
          relative group cursor-pointer overflow-hidden rounded-3xl bg-primary-50
          shadow-soft transition-shadow duration-500
          ${isHovered ? 'shadow-glow-primary' : ''}
        `}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={onClick}
      >
        {/* Loading Skeleton */}
        {!isLoaded && (
          <div className="absolute inset-0 overflow-hidden bg-primary-100/60">
            <div className="h-full w-full bg-gradient-to-r from-transparent via-white/60 to-transparent animate-shimmer" />
          </div>
        )}

        {/* Image */}
        <img
          src={photo.file_path}
          alt={`Wedding photo ${photo.photo_id}`}
          className={`w-full h-auto transition-transform duration-700 ease-out ${
            isLoaded ? 'opacity-100' : 'opacity-0'
          } ${isHovered ? 'scale-110' : 'scale-100'}`}
          onLoad={() => setIsLoaded(true)}
          loading="lazy"
        />

        {/* Gradient overlay on hover */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: isHovered ? 1 : 0 }}
          transition={{ duration: 0.3 }}
          className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/10 to-transparent"
        >
          <div className="absolute bottom-0 left-0 right-0 p-4">
            {photo.uploaded_at && (
              <div className="flex items-center gap-1.5 text-white/80 text-xs font-medium mb-3">
                <Calendar className="w-3 h-3" />
                <span>{formatDate(photo.uploaded_at)}</span>
              </div>
            )}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <motion.button
                  whileHover={{ scale: 1.12 }}
                  whileTap={{ scale: 0.9 }}
                  className={`p-2 rounded-full backdrop-blur-md transition-colors ${
                    isLiked ? 'bg-rose-500 text-white' : 'bg-white/20 hover:bg-white/30 text-white'
                  }`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsLiked((v) => !v);
                  }}
                >
                  <Heart className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`} />
                </motion.button>
                <motion.a
                  href={photo.file_path}
                  download
                  whileHover={{ scale: 1.12 }}
                  whileTap={{ scale: 0.9 }}
                  className="p-2 rounded-full bg-white/20 backdrop-blur-md hover:bg-white/30 text-white transition-colors"
                  onClick={(e) => e.stopPropagation()}
                >
                  <Download className="w-4 h-4" />
                </motion.a>
              </div>
              <div className="p-2 rounded-full bg-white/20 backdrop-blur-md">
                <ZoomIn className="w-4 h-4 text-white" />
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </motion.div>
  );
}
