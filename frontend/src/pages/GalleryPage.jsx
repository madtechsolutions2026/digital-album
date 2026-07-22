import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, Search, X, Loader2, Image as ImageIcon } from 'lucide-react';

import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import EmptyState from '../components/ui/EmptyState';
import { GallerySkeleton } from '../components/ui/Skeleton';
import MasonryGrid from '../components/gallery/MasonryGrid';
import SearchBar from '../components/search/SearchBar';
import { eventsAPI, photosAPI } from '../lib/api';

export default function GalleryPage() {
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [selectedPhoto, setSelectedPhoto] = useState(null);

  useEffect(() => {
    fetchEvents();
  }, []);

  useEffect(() => {
    if (selectedEventId) {
      fetchPhotos();
    }
  }, [selectedEventId]);

  const fetchEvents = async () => {
    try {
      const response = await eventsAPI.getAll();
      const eventList = response.data.data.events;
      setEvents(eventList);
      
      if (eventList.length > 0 && !selectedEventId) {
        setSelectedEventId(eventList[0].event_id);
      }
    } catch (error) {
      console.error('Failed to fetch events:', error);
    }
  };

  const fetchPhotos = async () => {
    if (!selectedEventId) return;
    
    setLoading(true);
    try {
      const response = await photosAPI.getByEvent(selectedEventId);
      setPhotos(response.data.data.photos || []);
    } catch (error) {
      console.error('Failed to fetch photos:', error);
      setPhotos([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (file) => {
    if (!selectedEventId) return;

    setSearching(true);
    const formData = new FormData();
    formData.append('selfie', file);

    try {
      const response = await photosAPI.searchByFace(formData, selectedEventId);
      setSearchResults(response.data.data.matches || []);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleClearSearch = () => {
    setSearchResults(null);
  };

  const displayPhotos = searchResults || photos;
  const selectedEvent = events.find(e => e.event_id === selectedEventId);

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div>
        <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-2">
          Wedding Gallery
        </h2>
        <p className="text-slate-600 dark:text-slate-400">
          Browse beautiful moments and find your photos with AI
        </p>
      </div>

      {/* Event Selector */}
      {events.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {events.map((event) => (
            <motion.button
              key={event.event_id}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                setSelectedEventId(event.event_id);
                setSearchResults(null);
              }}
              className={`
                px-6 py-3 rounded-xl font-medium transition-all
                ${selectedEventId === event.event_id
                  ? 'bg-primary-600 text-white shadow-soft-lg'
                  : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 shadow-soft'
                }
              `}
            >
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>{event.name}</span>
                <Badge variant={selectedEventId === event.event_id ? 'neutral' : 'neutral'}>
                  {event.photo_count}
                </Badge>
              </div>
            </motion.button>
          ))}
        </div>
      )}

      {/* Search Section */}
      {selectedEventId && (
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-1">
            <SearchBar onSearch={handleSearch} loading={searching} />
          </div>
          
          <div className="md:col-span-2">
            {searchResults && (
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                      Search Results
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Found {searchResults.length} photos
                    </p>
                  </div>
                  <Button
                    onClick={handleClearSearch}
                    variant="ghost"
                    icon={X}
                    size="sm"
                  >
                    Clear
                  </Button>
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Gallery Section */}
      <div>
        {!selectedEventId ? (
          <EmptyState
            icon={Calendar}
            title="No event selected"
            description="Select an event to view photos"
          />
        ) : loading ? (
          <GallerySkeleton />
        ) : displayPhotos.length === 0 ? (
          <EmptyState
            icon={ImageIcon}
            title={searchResults ? "No matches found" : "No photos yet"}
            description={
              searchResults
                ? "Try uploading a different selfie"
                : "Upload photos from the Admin page"
            }
          />
        ) : (
          <MasonryGrid 
            photos={displayPhotos} 
            onPhotoClick={setSelectedPhoto}
          />
        )}
      </div>

      {/* Photo Modal */}
      <AnimatePresence>
        {selectedPhoto && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
            onClick={() => setSelectedPhoto(null)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="relative max-w-4xl max-h-[90vh]"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setSelectedPhoto(null)}
                className="absolute -top-12 right-0 p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
              
              <img
                src={selectedPhoto.file_path}
                alt="Full size"
                className="max-w-full max-h-[90vh] rounded-2xl shadow-2xl"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
