import { motion, AnimatePresence } from 'framer-motion';
import { Search, Upload, X, Sparkles, ScanFace, CheckCircle2, RotateCcw } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import Button from '../ui/Button';

const SCAN_STEPS = [
  { label: 'Analyzing your photo' },
  { label: 'Detecting facial features' },
  { label: 'Matching against the gallery' },
];

export default function SearchBar({ onSearch, loading = false, resultCount = null, onReset }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const fileInputRef = useRef(null);

  // Cycle through the fake-but-honest progress timeline while searching.
  // The backend does one request/response with no granular progress, so
  // this communicates "work is happening" rather than exact real progress.
  useEffect(() => {
    if (!loading) {
      setActiveStep(0);
      return;
    }
    const interval = setInterval(() => {
      setActiveStep((s) => (s + 1) % SCAN_STEPS.length);
    }, 1100);
    return () => clearInterval(interval);
  }, [loading]);

  const selectFile = (file) => {
    if (!file || !file.type.startsWith('image/')) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleFileSelect = (e) => selectFile(e.target.files?.[0]);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    selectFile(e.dataTransfer.files?.[0]);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSearchAgain = () => {
    handleClear();
    onReset?.();
  };

  const handleSearch = () => {
    if (selectedFile) onSearch(selectedFile);
  };

  const showSuccess = resultCount !== null && !loading;

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="relative rounded-4xl bg-gradient-to-br from-primary-700 via-primary-600 to-primary-800 p-1 shadow-glow-primary overflow-hidden"
    >
      <div className="rounded-[calc(2rem-4px)] bg-white/95 backdrop-blur-xl p-6 md:p-10">
        <div className="grid md:grid-cols-5 gap-8 items-center">
          {/* Illustration */}
          <div className="hidden md:flex md:col-span-2 relative items-center justify-center h-full min-h-[260px]">
            <div className="absolute w-48 h-48 bg-gradient-to-br from-primary-400/30 to-gold-400/30 rounded-full blur-2xl animate-float" />
            <div className="relative">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
                className="w-40 h-40 rounded-full border-2 border-dashed border-primary-300"
              />
              <motion.div
                animate={{ rotate: -360 }}
                transition={{ duration: 26, repeat: Infinity, ease: 'linear' }}
                className="absolute inset-3 rounded-full border border-gold-300/70"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <motion.div
                  animate={{ scale: [1, 1.08, 1] }}
                  transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
                  className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary-600 to-gold-500 flex items-center justify-center shadow-glow-primary"
                >
                  <ScanFace className="w-10 h-10 text-white" />
                </motion.div>
              </div>
            </div>
          </div>

          {/* Upload / results */}
          <div className="md:col-span-3">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary-500 to-gold-500 shrink-0">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="font-display text-xl font-bold text-ink">
                  AI Face Search
                </h2>
                <p className="text-sm text-ink/60">
                  Upload a selfie and we'll find every photo you're in
                </p>
              </div>
            </div>

            <AnimatePresence mode="wait">
              {showSuccess ? (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.96 }}
                  className="text-center py-6"
                >
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 200, damping: 14, delay: 0.1 }}
                    className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4"
                  >
                    <CheckCircle2 className="w-9 h-9 text-emerald-600" />
                  </motion.div>
                  <h3 className="font-display text-lg font-bold text-ink mb-1">
                    {resultCount > 0
                      ? `Found ${resultCount} photo${resultCount === 1 ? '' : 's'} of you!`
                      : 'No matches found'}
                  </h3>
                  <p className="text-sm text-ink/60 mb-6">
                    {resultCount > 0
                      ? 'Scroll down to see your gallery'
                      : 'Try a different, clearer selfie'}
                  </p>
                  <Button onClick={handleSearchAgain} variant="ghost" icon={RotateCcw}>
                    Search Again
                  </Button>
                </motion.div>
              ) : loading ? (
                <motion.div
                  key="scanning"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="py-2"
                >
                  <div className="relative w-32 h-32 mx-auto mb-6 rounded-2xl overflow-hidden ring-2 ring-primary-300">
                    <img src={previewUrl} alt="Your selfie" className="w-full h-full object-cover" />
                    <motion.div
                      className="absolute left-0 right-0 h-8 bg-gradient-to-b from-primary-400/0 via-primary-300/60 to-primary-400/0"
                      animate={{ top: ['-10%', '100%'] }}
                      transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
                    />
                    <div className="absolute inset-0 border-2 border-primary-400/60 rounded-2xl" />
                  </div>

                  <div className="space-y-3 max-w-xs mx-auto">
                    {SCAN_STEPS.map((step, i) => (
                      <div key={step.label} className="flex items-center gap-3">
                        <div
                          className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 transition-colors duration-300 ${
                            i < activeStep
                              ? 'bg-emerald-500'
                              : i === activeStep
                              ? 'bg-primary-600'
                              : 'bg-primary-100'
                          }`}
                        >
                          {i < activeStep ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                          ) : i === activeStep ? (
                            <motion.div
                              animate={{ scale: [1, 1.3, 1] }}
                              transition={{ duration: 1, repeat: Infinity }}
                              className="w-2 h-2 rounded-full bg-white"
                            />
                          ) : null}
                        </div>
                        <span
                          className={`text-sm transition-colors duration-300 ${
                            i === activeStep ? 'text-ink font-medium' : 'text-ink/40'
                          }`}
                        >
                          {step.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              ) : !selectedFile ? (
                <motion.div
                  key="dropzone"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                  className={`relative rounded-3xl p-10 text-center cursor-pointer transition-colors ${
                    isDragging ? 'bg-primary-50' : 'bg-primary-50/40 hover:bg-primary-50/70'
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />

                  {/* Animated dashed border (marching ants via SMIL) */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none">
                    <rect
                      x="2" y="2" width="calc(100% - 4px)" height="calc(100% - 4px)"
                      rx="24" ry="24" fill="none"
                      stroke={isDragging ? '#7C3AED' : '#c4b5fd'}
                      strokeWidth="2"
                      strokeDasharray="10 8"
                      pathLength="100"
                    >
                      <animate attributeName="stroke-dashoffset" from="0" to="-100" dur="2.5s" repeatCount="indefinite" />
                    </rect>
                  </svg>

                  <motion.div
                    animate={{ y: [0, -8, 0] }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                    className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-gold-500 flex items-center justify-center mx-auto mb-4 shadow-glow-primary"
                  >
                    <Upload className="w-6 h-6 text-white" />
                  </motion.div>
                  <p className="text-ink font-medium mb-1">
                    Drag & drop your selfie here
                  </p>
                  <p className="text-sm text-ink/50">
                    or click to browse · JPG, PNG or WebP
                  </p>
                </motion.div>
              ) : (
                <motion.div
                  key="preview"
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="space-y-5"
                >
                  <div className="relative w-36 h-36 mx-auto rounded-2xl overflow-hidden ring-2 ring-primary-400 shadow-soft-lg">
                    <img src={previewUrl} alt="Selected selfie" className="w-full h-full object-cover" />
                    <button
                      onClick={handleClear}
                      className="absolute top-2 right-2 p-1.5 rounded-full bg-black/50 hover:bg-black/70 text-white transition-colors"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <Button
                    onClick={handleSearch}
                    variant="accent"
                    className="w-full"
                    icon={Search}
                  >
                    Find My Photos
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
