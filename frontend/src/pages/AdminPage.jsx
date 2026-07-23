import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Calendar, Sparkles, Trash2, X, Copy, Check, PartyPopper, AlertTriangle } from 'lucide-react';

import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import EventCard from '../components/ui/EventCard';
import DropZone from '../components/upload/DropZone';
import FilePreview from '../components/upload/FilePreview';
import UploadStatusPanel from '../components/upload/UploadStatusPanel';
import { eventsAPI, photosAPI, jobsAPI } from '../lib/api';
import { resizeImageFile } from '../lib/imageResize';

export default function AdminPage() {
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [showCreateEvent, setShowCreateEvent] = useState(false);
  const [newEventName, setNewEventName] = useState('');
  const [newEventDate, setNewEventDate] = useState('');
  const [uploadFiles, setUploadFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState({});
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });
  const [processingFaces, setProcessingFaces] = useState(false);
  const [processingFailed, setProcessingFailed] = useState(false);
  const [jobStatus, setJobStatus] = useState(null);
  const [showUploadPanel, setShowUploadPanel] = useState(false);
  const [deleteConfirmEvent, setDeleteConfirmEvent] = useState(null);
  const [deletingEventId, setDeletingEventId] = useState(null);
  const [deleteError, setDeleteError] = useState('');
  const [revealCredentials, setRevealCredentials] = useState(null);
  const [createError, setCreateError] = useState('');
  const [copiedField, setCopiedField] = useState(null);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await eventsAPI.getAll();
      setEvents(response.data.data.events);
      
      if (response.data.data.events.length > 0 && !selectedEventId) {
        setSelectedEventId(response.data.data.events[0].event_id);
      }
    } catch (error) {
      console.error('Failed to fetch events:', error);
    }
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    if (!newEventName || !newEventDate) return;

    setCreateError('');

    try {
      const response = await eventsAPI.create({
        name: newEventName,
        event_date: newEventDate
      });

      const { event_id, name, access_code, password } = response.data.data;

      await fetchEvents();
      setSelectedEventId(event_id);
      setNewEventName('');
      setNewEventDate('');
      setShowCreateEvent(false);

      // Show the one-time credential reveal - the password can't be
      // retrieved again after this.
      setRevealCredentials({ name, access_code, password });
    } catch (error) {
      console.error('Failed to create event:', error);
      setCreateError(
        error.response?.data?.message || error.response?.data?.detail?.[0]?.msg || 'Failed to create event. Please try again.'
      );
    }
  };

  const handleCopy = async (text, field) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch {
      // clipboard unavailable - nothing more we can do here
    }
  };

  const handleFilesSelected = (files) => {
    setUploadFiles(files);
    setUploadStatus({});
  };

  const handleUpload = async () => {
    if (!uploadFiles.length || !selectedEventId) return;

    setUploadLoading(true);
    setShowUploadPanel(true);
    setProcessingFailed(false);
    setJobStatus(null);
    setUploadProgress({ current: 0, total: uploadFiles.length });

    const BATCH_SIZE = 5;
    const newStatus = {};
    let successCount = 0;
    let errorCount = 0;

    for (let i = 0; i < uploadFiles.length; i += BATCH_SIZE) {
      const batch = uploadFiles.slice(i, i + BATCH_SIZE);
      
      await Promise.all(
        batch.map(async (file, batchIndex) => {
          const fileIndex = i + batchIndex;
          setUploadProgress({ current: fileIndex + 1, total: uploadFiles.length });
          
          newStatus[file.name] = { uploading: true };
          setUploadStatus({ ...newStatus });

          try {
            // Trim oversized originals client-side before upload - cuts
            // network transfer time and server-side decode cost. Falls
            // back to the original file if resizing fails for any reason.
            const uploadFile = await resizeImageFile(file);

            const formData = new FormData();
            formData.append('file', uploadFile);
            formData.append('event_id', selectedEventId);
            formData.append('skip_face_detection', 'true');

            await photosAPI.upload(formData);
            newStatus[file.name] = { success: true };
            successCount++;
          } catch (error) {
            newStatus[file.name] = { error: true };
            errorCount++;
          }
          
          setUploadStatus({ ...newStatus });
        })
      );
    }

    setUploadLoading(false);
    await fetchEvents();

    // Automatically kick off face processing so the event is searchable
    // without requiring a manual click.
    if (successCount > 0) {
      await handleProcessFaces(selectedEventId);
    }
  };

  const handleProcessFaces = async (eventId) => {
    if (!eventId) {
      console.error('No eventId provided to handleProcessFaces');
      return;
    }

    setProcessingFaces(true);
    setProcessingFailed(false);

    try {
      const response = await eventsAPI.processFaces(eventId);
      const jobId = response.data.data.job_id;
      await pollJobStatus(jobId);
    } catch (error) {
      console.error('Face processing failed:', error);
      setProcessingFaces(false);
      setProcessingFailed(true);
    }
  };

  const pollJobStatus = async (jobId) => {
    const checkStatus = async () => {
      try {
        const response = await jobsAPI.getStatus(jobId);
        const { status, progress } = response.data;

        if (progress) {
          setJobStatus(progress);
        }

        if (status === 'success') {
          setProcessingFaces(false);
          await fetchEvents();
          return true;
        } else if (status === 'failure') {
          setProcessingFaces(false);
          setProcessingFailed(true);
          return true;
        } else {
          setTimeout(checkStatus, 2000);
        }
      } catch (error) {
        console.error('Error checking job status:', error);
        setTimeout(checkStatus, 2000);
      }
    };

    await checkStatus();
  };

  const handleDeleteEvent = async () => {
    if (!deleteConfirmEvent) return;

    setDeletingEventId(deleteConfirmEvent.event_id);
    setDeleteError('');

    try {
      await eventsAPI.delete(deleteConfirmEvent.event_id);

      if (selectedEventId === deleteConfirmEvent.event_id) {
        setSelectedEventId(null);
      }

      setDeleteConfirmEvent(null);
      await fetchEvents();
    } catch (error) {
      console.error('Failed to delete event:', error);
      setDeleteError(
        error.response?.data?.detail || 'Failed to delete event. Please try again.'
      );
    } finally {
      setDeletingEventId(null);
    }
  };

  const selectedEvent = events.find(e => e.event_id === selectedEventId);

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-primary-600 font-semibold text-sm tracking-wide uppercase mb-1">
            Studio
          </p>
          <h2 className="font-display text-3xl md:text-4xl font-bold text-ink mb-2">
            Admin Studio
          </h2>
          <p className="text-ink/60">
            Manage events, upload photos, and process faces
          </p>
        </div>

        <Button
          onClick={() => setShowCreateEvent(!showCreateEvent)}
          variant="accent"
          icon={Plus}
        >
          New Event
        </Button>
      </div>

      {/* Create Event Form */}
      <AnimatePresence>
        {showCreateEvent && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card className="p-6">
              <form onSubmit={handleCreateEvent} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Event Name
                  </label>
                  <input
                    type="text"
                    value={newEventName}
                    onChange={(e) => setNewEventName(e.target.value)}
                    placeholder="John & Jane's Wedding"
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Wedding Date
                  </label>
                  <input
                    type="date"
                    value={newEventDate}
                    onChange={(e) => setNewEventDate(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                    required
                  />
                </div>

                {createError && (
                  <p className="text-sm text-rose-600">{createError}</p>
                )}

                <div className="flex gap-3">
                  <Button type="submit" variant="primary">
                    Create Event
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setShowCreateEvent(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Events Grid */}
      <div>
        <h3 className="font-display text-lg font-bold text-ink mb-4">
          Your Events
        </h3>

        {events.length === 0 ? (
          <EmptyState
            icon={Calendar}
            title="No events yet"
            description="Create your first event to start uploading photos"
            action={() => setShowCreateEvent(true)}
            actionLabel="Create Event"
          />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-5">
            {events.map((event) => (
              <EventCard
                key={event.event_id}
                event={event}
                isSelected={selectedEventId === event.event_id}
                onClick={() => setSelectedEventId(event.event_id)}
                onDelete={(evt) => {
                  setDeleteError('');
                  setDeleteConfirmEvent(evt);
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Upload Section */}
      {selectedEventId && (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Upload Photos
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Uploading to: <span className="font-medium">{selectedEvent?.name}</span>
            </p>
          </div>

          <DropZone onFilesSelected={handleFilesSelected} />

          {uploadFiles.length > 0 && (
            <div className="space-y-4">
              <FilePreview
                files={uploadFiles}
                onRemove={(index) => {
                  const newFiles = [...uploadFiles];
                  newFiles.splice(index, 1);
                  setUploadFiles(newFiles);
                }}
                uploadStatus={uploadStatus}
              />

              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {uploadFiles.length} files ready to upload
                </p>
                <div className="flex gap-3">
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setUploadFiles([]);
                      setUploadStatus({});
                    }}
                  >
                    Clear All
                  </Button>
                  <Button
                    onClick={handleUpload}
                    loading={uploadLoading}
                    variant="accent"
                    icon={Sparkles}
                  >
                    Upload & Process
                  </Button>
                </div>
              </div>
            </div>
          )}

          <UploadStatusPanel
            isVisible={showUploadPanel}
            uploading={uploadLoading}
            uploadProgress={uploadProgress}
            successCount={Object.values(uploadStatus).filter(s => s.success).length}
            errorCount={Object.values(uploadStatus).filter(s => s.error).length}
            processingFaces={processingFaces}
            processingFailed={processingFailed}
            jobStatus={jobStatus}
            onClose={() => {
              setShowUploadPanel(false);
              setUploadFiles([]);
              setUploadStatus({});
              setJobStatus(null);
              setProcessingFailed(false);
            }}
          />
        </div>
      )}

      {/* Delete Event Confirmation */}
      <AnimatePresence>
        {deleteConfirmEvent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            onClick={() => !deletingEventId && setDeleteConfirmEvent(null)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 10 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 10 }}
              className="glass-card max-w-sm w-full p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-full bg-rose-100 dark:bg-rose-900/30">
                  <Trash2 className="w-5 h-5 text-rose-600 dark:text-rose-400" />
                </div>
                {!deletingEventId && (
                  <button
                    onClick={() => setDeleteConfirmEvent(null)}
                    className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    <X className="w-4 h-4 text-slate-500" />
                  </button>
                )}
              </div>

              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                Delete "{deleteConfirmEvent.name}"?
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
                This permanently deletes {deleteConfirmEvent.photo_count} photo{deleteConfirmEvent.photo_count === 1 ? '' : 's'},
                their face data, and the image files stored in Cloudflare. This cannot be undone.
              </p>

              {deleteError && (
                <p className="text-sm text-rose-600 dark:text-rose-400 mb-4">
                  {deleteError}
                </p>
              )}

              <div className="flex gap-3">
                <Button
                  variant="ghost"
                  onClick={() => setDeleteConfirmEvent(null)}
                  disabled={!!deletingEventId}
                >
                  Cancel
                </Button>
                <Button
                  variant="danger"
                  onClick={handleDeleteEvent}
                  loading={!!deletingEventId}
                  className="flex-1"
                >
                  {deletingEventId ? 'Deleting...' : 'Delete Permanently'}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* One-time credential reveal after creating an event */}
      <AnimatePresence>
        {revealCredentials && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/60 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, y: 10 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 10 }}
              className="relative rounded-4xl bg-gradient-to-br from-primary-600 via-primary-500 to-gold-500 p-1 shadow-glow-primary max-w-sm w-full"
            >
              <div className="rounded-[calc(2rem-4px)] bg-white px-7 py-8">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-600 to-gold-500 flex items-center justify-center mx-auto mb-4 shadow-glow-primary">
                  <PartyPopper className="w-7 h-7 text-white" />
                </div>

                <h3 className="font-display text-xl font-bold text-ink text-center mb-1">
                  "{revealCredentials.name}" is live
                </h3>
                <p className="text-sm text-ink/60 text-center mb-6">
                  Share these with the couple so they can unlock their gallery
                </p>

                <div className="space-y-3 mb-5">
                  <div>
                    <p className="text-xs font-semibold text-ink/40 uppercase tracking-wide mb-1.5">
                      Event Code
                    </p>
                    <button
                      onClick={() => handleCopy(revealCredentials.access_code, 'code')}
                      className="w-full flex items-center justify-between px-4 py-3 rounded-2xl bg-primary-50 border border-primary-100 hover:bg-primary-100/60 transition-colors"
                    >
                      <span className="font-mono font-bold text-ink tracking-widest">
                        {revealCredentials.access_code}
                      </span>
                      {copiedField === 'code' ? (
                        <Check className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <Copy className="w-4 h-4 text-ink/40" />
                      )}
                    </button>
                  </div>

                  <div>
                    <p className="text-xs font-semibold text-ink/40 uppercase tracking-wide mb-1.5">
                      Password
                    </p>
                    <button
                      onClick={() => handleCopy(revealCredentials.password, 'password')}
                      className="w-full flex items-center justify-between px-4 py-3 rounded-2xl bg-primary-50 border border-primary-100 hover:bg-primary-100/60 transition-colors"
                    >
                      <span className="font-mono font-bold text-ink tracking-widest">
                        {revealCredentials.password}
                      </span>
                      {copiedField === 'password' ? (
                        <Check className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <Copy className="w-4 h-4 text-ink/40" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="flex items-start gap-2 px-3.5 py-2.5 rounded-xl bg-gold-50 text-gold-800 text-xs mb-6">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  Save this now - the password can't be shown again after you close this.
                </div>

                <Button
                  variant="primary"
                  onClick={() => setRevealCredentials(null)}
                  className="w-full"
                >
                  Done
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
