import { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Calendar, Image as ImageIcon, LogOut } from 'lucide-react';

import EmptyState from '../components/ui/EmptyState';
import { GallerySkeleton } from '../components/ui/Skeleton';
import MasonryGrid from '../components/gallery/MasonryGrid';
import PhotoModal from '../components/gallery/PhotoModal';
import AccessCard from '../components/gallery/AccessCard';
import SearchBar from '../components/search/SearchBar';
import { photosAPI } from '../lib/api';
import { getGallerySession, saveGallerySession, clearGallerySession } from '../lib/gallerySession';

function formatWeddingDate(dateStr) {
  if (!dateStr) return null;
  return new Date(dateStr).toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function GalleryPage() {
  const [session, setSession] = useState(() => getGallerySession());
  const [photos, setPhotos] = useState([]);
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [activeCategory, setActiveCategory] = useState('All');

  useEffect(() => {
    if (session) fetchPhotos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.event_id]);

  const handleSessionExpired = () => {
    clearGallerySession();
    setSession(null);
    setPhotos([]);
    setSearchResults(null);
  };

  const fetchPhotos = async () => {
    if (!session) return;

    setLoading(true);
    try {
      const response = await photosAPI.getByEvent(session.event_id);
      setPhotos(response.data.data.photos || []);
    } catch (error) {
      if (error.response?.status === 401 || error.response?.status === 403) {
        handleSessionExpired();
      } else {
        console.error('Failed to fetch photos:', error);
        setPhotos([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUnlock = (newSession) => {
    saveGallerySession(newSession);
    setSession(newSession);
  };

  const handleSwitchEvent = () => {
    handleSessionExpired();
  };

  const handleSearch = async (file) => {
    if (!session) return;

    setSearching(true);
    const formData = new FormData();
    formData.append('selfie', file);

    try {
      const response = await photosAPI.searchByFace(formData, session.event_id);
      setSearchResults(response.data.data.matches || []);
    } catch (error) {
      if (error.response?.status === 401 || error.response?.status === 403) {
        handleSessionExpired();
      } else {
        console.error('Search failed:', error);
        setSearchResults([]);
      }
    } finally {
      setSearching(false);
    }
  };

  const handleClearSearch = () => setSearchResults(null);

  // Categories come from the folder name photos were uploaded under
  // (see AdminPage's folder upload). Only shown while browsing - face
  // search results span the whole event regardless of category.
  const categories = ['All', ...new Set(
    photos.map((p) => p.photo_metadata?.category).filter(Boolean)
  )];
  const categorizedPhotos = activeCategory === 'All'
    ? photos
    : photos.filter((p) => p.photo_metadata?.category === activeCategory);

  const displayPhotos = searchResults || categorizedPhotos;
  const coverImage = session?.cover_photo || (photos[0]?.file_path ?? null);

  // Not unlocked yet - show the access card, same as the homepage
  if (!session) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <AccessCard onUnlock={handleUnlock} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 -mt-32">
      {/* Private gallery hero - breaks out to full viewport width regardless
          of the parent max-w-7xl container, for a true cinematic hero */}
      <div className="relative left-1/2 right-1/2 -mx-[50vw] w-screen rounded-b-[2.5rem] overflow-hidden">
        <div
          className="relative min-h-[60vh] flex items-end bg-gradient-to-br from-[#1a1025] via-[#2a1454] to-[#3b1d63] bg-cover bg-center"
          style={coverImage ? { backgroundImage: `linear-gradient(to top, rgba(26,16,37,0.92), rgba(26,16,37,0.35)), url(${coverImage})` } : undefined}
        >
          <button
            onClick={handleSwitchEvent}
            className="absolute top-28 right-6 z-10 flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-white/80 text-xs font-medium hover:bg-white/20 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            Switch Event
          </button>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="relative w-full max-w-5xl mx-auto px-6 pt-40 pb-14 text-center"
          >
            <p className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-gold-300 text-xs font-semibold tracking-wide uppercase mb-5">
              Your Private Gallery
            </p>
            <h1 className="font-display text-4xl md:text-5xl font-extrabold text-white mb-3 text-balance">
              {session.name}
            </h1>
            {session.event_date && (
              <p className="flex items-center justify-center gap-2 text-white/70 text-lg">
                <Calendar className="w-4 h-4" />
                {formatWeddingDate(session.event_date)}
              </p>
            )}
          </motion.div>
        </div>
      </div>

      {/* AI Face Search centerpiece */}
      <SearchBar
        onSearch={handleSearch}
        loading={searching}
        resultCount={searchResults ? searchResults.length : null}
        onReset={handleClearSearch}
      />

      {/* Category Tabs */}
      {!searchResults && categories.length > 2 && (
        <div className="flex flex-wrap items-center justify-center gap-2">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-4 py-2 rounded-full text-sm font-medium uppercase tracking-wide transition-colors ${
                activeCategory === cat
                  ? 'bg-primary-600 text-white shadow-glow-primary'
                  : 'bg-primary-50 text-ink/60 hover:bg-primary-100'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      {/* Gallery Section */}
      <div>
        {loading ? (
          <GallerySkeleton />
        ) : displayPhotos.length === 0 ? (
          <EmptyState
            icon={ImageIcon}
            title={searchResults ? 'No matches found' : 'Photos are on their way'}
            description={
              searchResults
                ? 'Try uploading a different, clearer selfie'
                : "Your photographer hasn't uploaded photos yet - check back soon"
            }
          />
        ) : (
          <MasonryGrid
            photos={displayPhotos}
            onPhotoClick={(photo) =>
              setSelectedIndex(displayPhotos.findIndex((p) => p.photo_id === photo.photo_id))
            }
          />
        )}
      </div>

      {/* Photo Modal */}
      <AnimatePresence>
        {selectedIndex !== null && (
          <PhotoModal
            photos={displayPhotos}
            index={selectedIndex}
            onClose={() => setSelectedIndex(null)}
            onNavigate={setSelectedIndex}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
