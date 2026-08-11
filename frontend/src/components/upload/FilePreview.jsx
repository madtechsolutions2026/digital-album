import { motion } from 'framer-motion';
import { X, File, Image as ImageIcon } from 'lucide-react';
import { getFileCategory } from '../../lib/fileCategory';

export default function FilePreview({ files, onRemove, uploadStatus = {} }) {
  if (!files || files.length === 0) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      {files.map((file, index) => {
        const status = uploadStatus[file.name];
        const isError = status?.error;
        const isUploading = status?.uploading;
        // Uploaded thumbnail (compressed R2 WebP) once available - avoids ever
        // decoding the raw local file (300-400/folder would spike memory).
        const uploadedUrl = status?.url;
        const category = getFileCategory(file);

        return (
          <motion.div
            key={`${file.name}-${index}`}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ delay: index * 0.05 }}
            className="relative group"
          >
            <div className="relative aspect-square rounded-xl overflow-hidden bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              {uploadedUrl ? (
                <img
                  src={uploadedUrl}
                  alt={file.name}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  {file.type?.startsWith('image/') ? (
                    <ImageIcon className="w-8 h-8 text-slate-400" />
                  ) : (
                    <File className="w-8 h-8 text-slate-400" />
                  )}
                </div>
              )}

              {/* Upload Status Overlay */}
              {isUploading && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                  <div className="w-8 h-8 border-4 border-white/30 border-t-white rounded-full animate-spin" />
                </div>
              )}

              {isError && (
                <div className="absolute inset-0 bg-rose-500/20 flex items-center justify-center">
                  <X className="w-8 h-8 text-rose-500" />
                </div>
              )}

              {/* Category Badge */}
              {category && (
                <span className="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-black/60 text-white text-[10px] font-medium truncate max-w-[80%]">
                  {category}
                </span>
              )}

              {/* Remove Button */}
              {!isUploading && onRemove && (
                <button
                  onClick={() => onRemove(index)}
                  className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/50 hover:bg-black/70 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* File Name */}
            <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 truncate">
              {file.name}
            </p>
          </motion.div>
        );
      })}
    </div>
  );
}
