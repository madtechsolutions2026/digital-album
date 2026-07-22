import { motion } from 'framer-motion';
import { Search, Upload, X, Sparkles } from 'lucide-react';
import { useState, useRef } from 'react';
import Button from '../ui/Button';

export default function SearchBar({ onSearch, loading = false }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSearch = () => {
    if (selectedFile) {
      onSearch(selectedFile);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="p-3 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            AI Face Search
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Upload a selfie to find all photos with that person
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {/* File Upload Area */}
        {!selectedFile ? (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-8 text-center cursor-pointer hover:border-primary-500 dark:hover:border-primary-500 transition-colors"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Upload className="w-8 h-8 text-slate-400 mx-auto mb-3" />
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Click to upload a selfie
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
              JPG, PNG or WebP
            </p>
          </div>
        ) : (
          <div className="relative">
            <div className="relative aspect-square max-w-xs mx-auto rounded-xl overflow-hidden border-2 border-primary-500">
              <img
                src={previewUrl}
                alt="Selected photo"
                className="w-full h-full object-cover"
              />
              <button
                onClick={handleClear}
                className="absolute top-2 right-2 p-2 rounded-lg bg-black/50 hover:bg-black/70 text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Search Button */}
        {selectedFile && (
          <Button
            onClick={handleSearch}
            loading={loading}
            variant="accent"
            className="w-full"
            icon={Search}
          >
            {loading ? 'Searching...' : 'Find My Photos'}
          </Button>
        )}
      </div>
    </motion.div>
  );
}
