import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Loader2, Circle, AlertCircle, X, Sparkles } from 'lucide-react';
import Card from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';
import Badge from '../ui/Badge';

function StepIcon({ state }) {
  if (state === 'done') {
    return (
      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900/30 shrink-0">
        <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
      </div>
    );
  }
  if (state === 'active') {
    return (
      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 shrink-0">
        <Loader2 className="w-5 h-5 text-primary-600 dark:text-primary-400 animate-spin" />
      </div>
    );
  }
  if (state === 'error') {
    return (
      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-rose-100 dark:bg-rose-900/30 shrink-0">
        <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
      </div>
    );
  }
  return (
    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 shrink-0">
      <Circle className="w-4 h-4 text-slate-400 dark:text-slate-600" />
    </div>
  );
}

// Face detection is temporarily disabled from the upload flow (memory
// pressure on the backend - InsightFace is heavy and was triggering on
// every upload). Uploads still work; face processing is just not
// auto-triggered or shown here for now. Flip this back to true - and the
// auto-trigger in AdminPage.jsx's handleUpload - to re-enable.
const FACE_DETECTION_ENABLED = false;

export default function UploadStatusPanel({
  isVisible,
  uploading,
  uploadProgress,
  successCount,
  errorCount,
  processingFaces,
  processingFailed,
  jobStatus,
  onClose,
}) {
  if (!isVisible) return null;

  const uploadTotal = uploadProgress.total || 0;
  const uploadCurrent = uploadProgress.current || 0;
  const uploadComplete = uploadTotal > 0 && uploadCurrent === uploadTotal && !uploading;
  const uploadState = uploading ? 'active' : uploadComplete ? 'done' : 'pending';

  const faceTotal = jobStatus?.total || 0;
  const faceCurrent = jobStatus?.current || 0;
  const faceComplete = uploadComplete && !processingFaces && jobStatus?.status === 'Complete';

  const faceState = processingFailed
    ? 'error'
    : processingFaces
    ? 'active'
    : faceComplete
    ? 'done'
    : 'pending';

  const allDone = FACE_DETECTION_ENABLED
    ? uploadComplete && (faceComplete || processingFailed)
    : uploadComplete;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -12, height: 0 }}
        animate={{ opacity: 1, y: 0, height: 'auto' }}
        exit={{ opacity: 0, y: -12, height: 0 }}
        transition={{ duration: 0.25 }}
      >
        <Card className="p-6 relative" hover={false}>
          {allDone && onClose && (
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-4 h-4 text-slate-500" />
            </button>
          )}

          <h4 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-5">
            {allDone ? 'Upload complete' : 'Uploading & processing photos'}
          </h4>

          <div className="space-y-6">
            {/* Step 1: Upload */}
            <div className="flex gap-4">
              <div className="flex flex-col items-center">
                <StepIcon state={uploadState} />
                <div className="w-px flex-1 bg-slate-200 dark:bg-slate-700 mt-2" />
              </div>
              <div className="flex-1 pb-2">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    Uploading photos
                  </span>
                  <span className="text-sm text-slate-500 dark:text-slate-400">
                    {uploadCurrent} / {uploadTotal}
                  </span>
                </div>
                <ProgressBar value={uploadCurrent} max={uploadTotal || 1} showPercentage={false} />
                {(successCount > 0 || errorCount > 0) && (
                  <div className="flex items-center gap-2 mt-2">
                    {successCount > 0 && <Badge variant="success">{successCount} uploaded</Badge>}
                    {errorCount > 0 && <Badge variant="error">{errorCount} failed</Badge>}
                  </div>
                )}
              </div>
            </div>

            {/* Step 2: Face processing - hidden while FACE_DETECTION_ENABLED is false */}
            {FACE_DETECTION_ENABLED && (
              <div className="flex gap-4">
                <StepIcon state={faceState} />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                      Detecting faces
                    </span>
                    {faceTotal > 0 && (
                      <span className="text-sm text-slate-500 dark:text-slate-400">
                        {faceCurrent} / {faceTotal}
                      </span>
                    )}
                  </div>
                  {faceTotal > 0 || processingFaces ? (
                    <ProgressBar value={faceCurrent} max={faceTotal || 1} showPercentage={false} />
                  ) : (
                    <p className="text-sm text-slate-400 dark:text-slate-500">
                      Waiting for upload to finish...
                    </p>
                  )}
                  {jobStatus?.faces_found > 0 && (
                    <p className="text-xs text-slate-500 dark:text-slate-500 mt-2">
                      {jobStatus.faces_found} faces found so far
                    </p>
                  )}
                  {processingFailed && (
                    <p className="text-xs text-rose-600 dark:text-rose-400 mt-2">
                      Face processing failed. Retry from the event card once ready.
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {FACE_DETECTION_ENABLED && faceComplete && (
            <div className="mt-5 pt-4 border-t border-slate-200 dark:border-slate-700 flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
              <Sparkles className="w-4 h-4" />
              Photos are searchable in the gallery now.
            </div>
          )}
        </Card>
      </motion.div>
    </AnimatePresence>
  );
}
