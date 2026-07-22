import { motion } from 'framer-motion';
import { X, File, CheckCircle2 } from 'lucide-react';

export default function FilePreview({ files, onRemove, uploadStatus = {} }) {
  if (!files || files.length === 0) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      {files.map((file, index) => {
        const isSuccess = uploadStatus[file.name]?.success;
        const isError = uploadStatus[file.name]?.error;
        const isUploading = uploadStatus[file.name]?.uploading;

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
              {file.type?.startsWith('image/') ? (
                <img
                  src={URL.createObjectURL(file)}
                  alt={file.name}
                  className="w-full h-full object-cover"
                  onLoad={(e) => URL.revokeObjectURL(e.target.src)}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <File className="w-8 h-8 text-slate-400" />
                </div>
              )}

              {/* Upload Status Overlay */}
              {isUploading && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                  <div className="w-8 h-8 border-4 border-white/30 border-t-white rounded-full animate-spin" />
                </div>
              )}

              {isSuccess && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute inset-0 bg-emerald-500/20 flex items-center justify-center"
                >
                  <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                </motion.div>
              )}

              {isError && (
                <div className="absolute inset-0 bg-rose-500/20 flex items-center justify-center">
                  <X className="w-8 h-8 text-rose-500" />
                </div>
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
