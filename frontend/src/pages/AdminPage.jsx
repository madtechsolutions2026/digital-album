import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Calendar, Image as ImageIcon, Sparkles, Trash2, X } from 'lucide-react';

import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import EmptyState from '../components/ui/EmptyState';
import DropZone from '../components/upload/DropZone';
import FilePreview from '../components/upload/FilePreview';
import UploadStatusPanel from '../components/upload/UploadStatusPanel';
import { eventsAPI, photosAPI, jobsAPI } from '../lib/api';

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
    if (!newEventName) return;

    try {
      const response = await eventsAPI.create({
        name: newEventName,
        event_date: newEventDate || null
      });
      
      await fetchEvents();
      setSelectedEventId(response.data.data.event_id);
      setNewEventName('');
      setNewEventDate('');
      setShowCreateEvent(false);
    } catch (error) {
      console.error('Failed to create event:', error);
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

          const formData = new FormData();
          formData.append('file', file);
          formData.append('event_id', selectedEventId);
          formData.append('skip_face_detection', 'true');

          try {
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
          <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-2">
            Admin Studio
          </h2>
          <p className="text-slate-600 dark:text-slate-400">
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
                    Event Date (Optional)
                  </label>
                  <input
                    type="date"
                    value={newEventDate}
                    onChange={(e) => setNewEventDate(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  />
                </div>
                
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
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {events.map((event) => (
              <Card
                key={event.event_id}
                className={`p-6 cursor-pointer transition-all ${
                  selectedEventId === event.event_id
                    ? 'ring-2 ring-primary-500'
                    : ''
                }`}
                onClick={() => setSelectedEventId(event.event_id)}
              >
                <div className="flex items-start justify-between mb-3">
                  <h4 className="font-semibold text-slate-900 dark:text-slate-100">
                    {event.name}
                  </h4>
                  <div className="flex items-center gap-2">
                    {selectedEventId === event.event_id && (
                      <Badge variant="primary">Selected</Badge>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeleteError('');
                        setDeleteConfirmEvent(event);
                      }}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-900/20 transition-colors"
                      aria-label={`Delete ${event.name}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                {event.event_date && (
                  <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 mb-3">
                    <Calendar className="w-4 h-4" />
                    <span>{new Date(event.event_date).toLocaleDateString()}</span>
                  </div>
                )}
                
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400">
                    <ImageIcon className="w-4 h-4" />
                    <span>{event.photo_count} photos</span>
                  </div>
                </div>
              </Card>
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
    </div>
  );
}
