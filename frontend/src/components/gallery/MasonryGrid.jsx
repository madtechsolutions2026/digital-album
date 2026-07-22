import { motion } from 'framer-motion';
import { useState } from 'react';
import { Heart, Download, ZoomIn } from 'lucide-react';

export default function MasonryGrid({ photos, onPhotoClick }) {
  return (
    <div className="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
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

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="break-inside-avoid mb-4"
    >
      <div
        className="relative group cursor-pointer overflow-hidden rounded-2xl bg-slate-100 dark:bg-slate-800"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={onClick}
      >
        {/* Loading Skeleton */}
        {!isLoaded && (
          <div className="absolute inset-0 animate-pulse bg-slate-200 dark:bg-slate-700" />
        )}

        {/* Image */}
        <img
          src={photo.file_path}
          alt={`Photo ${photo.photo_id}`}
          className={`w-full h-auto transition-all duration-500 ${
            isLoaded ? 'opacity-100' : 'opacity-0'
          } ${isHovered ? 'scale-105' : 'scale-100'}`}
          onLoad={() => setIsLoaded(true)}
          loading="lazy"
        />

        {/* Overlay on Hover */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: isHovered ? 1 : 0 }}
          className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent"
        >
          <div className="absolute bottom-0 left-0 right-0 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="p-2 rounded-lg bg-white/20 backdrop-blur-sm hover:bg-white/30 transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Handle like
                  }}
                >
                  <Heart className="w-4 h-4 text-white" />
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="p-2 rounded-lg bg-white/20 backdrop-blur-sm hover:bg-white/30 transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Handle download
                  }}
                >
                  <Download className="w-4 h-4 text-white" />
                </motion.button>
              </div>
              <div className="p-2 rounded-lg bg-white/20 backdrop-blur-sm">
                <ZoomIn className="w-4 h-4 text-white" />
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
