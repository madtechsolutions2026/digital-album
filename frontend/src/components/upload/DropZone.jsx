import { useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';
import { Upload, Image as ImageIcon, FolderOpen, File } from 'lucide-react';
import Button from '../ui/Button';

export default function DropZone({ onFilesSelected, accept = 'image/*', multiple = true }) {
  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);

  const onDrop = useCallback((acceptedFiles) => {
    onFilesSelected(acceptedFiles);
  }, [onFilesSelected]);

  const { getRootProps, getInputProps, isDragActive, isDragAccept, isDragReject } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpeg', '.jpg', '.png', '.webp'] },
    multiple,
    noClick: true, // Disable default click to use our custom buttons
  });

  const handleFileSelect = (e) => {
    e.stopPropagation();
    fileInputRef.current?.click();
  };

  const handleFolderSelect = (e) => {
    e.stopPropagation();
    folderInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      onFilesSelected(files);
    }
  };

  return (
    <motion.div
      {...getRootProps()}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      className={`
        relative overflow-hidden
        border-2 border-dashed rounded-3xl
        p-12 cursor-default
        transition-all duration-300
        ${isDragActive
          ? 'border-primary-500 bg-primary-50'
          : 'border-primary-200 hover:border-primary-400 bg-primary-50/30'
        }
        ${isDragAccept ? 'border-emerald-500 bg-emerald-50' : ''}
        ${isDragReject ? 'border-rose-500 bg-rose-50' : ''}
      `}
    >
      {/* Hidden inputs */}
      <input
        {...getInputProps()}
        style={{ display: 'none' }}
      />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        multiple
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
      <input
        ref={folderInputRef}
        type="file"
        accept="image/*"
        webkitdirectory="true"
        directory="true"
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
      
      <div className="flex flex-col items-center justify-center gap-6 text-center">
        <motion.div
          animate={isDragActive ? { scale: 1.1, rotate: 5 } : { scale: 1, rotate: 0 }}
          className="p-6 rounded-2xl bg-gradient-to-br from-primary-600 to-gold-500 shadow-glow-primary"
        >
          {isDragActive ? (
            <FolderOpen className="w-12 h-12 text-white" />
          ) : (
            <Upload className="w-12 h-12 text-white" />
          )}
        </motion.div>

        <div>
          <h3 className="font-display text-lg font-bold text-ink mb-2">
            {isDragActive ? 'Drop your photos here' : 'Upload Wedding Photos'}
          </h3>
          <p className="text-sm text-ink/60 mb-4">
            Drag and drop images or folder, or click below to browse
          </p>

          {/* Upload buttons */}
          <div className="flex items-center justify-center gap-3">
            <Button
              onClick={handleFileSelect}
              variant="primary"
              icon={File}
              size="sm"
            >
              Select Files
            </Button>
            <Button
              onClick={handleFolderSelect}
              variant="accent"
              icon={FolderOpen}
              size="sm"
            >
              Select Folder
            </Button>
          </div>

          <p className="text-xs text-ink/40 mt-4">
            Supports: JPG, PNG, WebP • Max 10MB per file
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs text-ink/40">
          <div className="flex items-center gap-2">
            <ImageIcon className="w-4 h-4" />
            <span>High Quality</span>
          </div>
          <div className="w-1 h-1 rounded-full bg-primary-200" />
          <div className="flex items-center gap-2">
            <span>Fast Upload</span>
          </div>
          <div className="w-1 h-1 rounded-full bg-primary-200" />
          <div className="flex items-center gap-2">
            <span>Secure Storage</span>
          </div>
        </div>
      </div>

      {/* Animated border glow on hover */}
      <div className="absolute inset-0 rounded-3xl opacity-0 hover:opacity-100 transition-opacity duration-500 pointer-events-none">
        <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-primary-500/20 via-gold-500/20 to-primary-500/20 animate-shimmer" />
      </div>
    </motion.div>
  );
}
