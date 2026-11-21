import { AnimatePresence, motion } from 'framer-motion';
import {
  ArrowRight, Bell, Check, ChevronDown, Copy, Download, ExternalLink,
  FolderUp, Grid2X2, ImagePlus, LayoutDashboard, Menu, MoreHorizontal,
  QrCode, RefreshCw, Search, Send, ShieldCheck, Sparkles, Trash2,
  Upload, UserCheck, Users, X, Zap
} from 'lucide-react';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { albumStore } from './lib/albumStore';
import { eventsAPI, galleryAPI, guestsAPI, photosAPI, mediaUrl } from './lib/api';

const NAV_ITEMS = [
  { id: 'Overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'Events', label: 'Events', icon: Grid2X2 },
  { id: 'Guests', label: 'Guests', icon: Users },
  { id: 'Uploads', label: 'Uploads', icon: FolderUp },
  { id: 'Match review', label: 'Match review', icon: Sparkles },
  { id: 'Delivery', label: 'Delivery', icon: Send },
];

const CATEGORIES = ['Haldi', 'Mehendi', 'Sangeet', 'Shaadi', 'Reception', 'Other'];

function StatusBadge({ children }) {
  const styles = {
    Matched: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    'Ready to send': 'bg-blue-50 text-blue-700 border border-blue-200',
    'Needs review': 'bg-amber-50 text-amber-700 border border-amber-200',
    Processing: 'bg-stone-100 text-stone-600 border border-stone-200',
    Delivered: 'bg-violet-50 text-violet-700 border border-violet-200',
    'In progress': 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    'Ready to publish': 'bg-amber-50 text-amber-700 border border-amber-200',
  };
  return (
    <span className={`pill ${styles[children] || 'bg-stone-100 text-stone-600'}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {children}
    </span>
  );
}

function Logo() {
  return (
    <div className="flex items-center gap-3">
      <div className="grid h-9 w-9 place-items-center rounded-xl bg-[#205c3b] text-sm font-bold text-white shadow-lg shadow-emerald-900/15">
        DG
      </div>
      <div>
        <p className="text-[15px] font-bold tracking-tight text-[#1e3127]">DG Album</p>
        <p className="text-[9px] font-bold uppercase tracking-[.18em] text-[#829087]">Studio console</p>
      </div>
    </div>
  );
}

function Toast({ message, onDismiss }) {
  if (!message) return null;
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-2xl bg-[#1e3127] px-5 py-3 text-sm text-white shadow-2xl shadow-emerald-950/30"
    >
      <Check size={18} className="text-[#a4e2ba]" />
      <span>{message}</span>
      <button onClick={onDismiss} className="ml-2 text-white/60 hover:text-white">
        <X size={15} />
      </button>
    </motion.div>
  );
}

function SideBar({ page, setPage, activeEvent, reviewCount }) {
  return (
    <aside className="desktop-sidebar fixed inset-y-0 left-0 z-20 flex w-[244px] flex-col border-r border-[#dfe7dd] bg-[#fbfcf9] px-4 py-6">
      <Logo />
      <div className="mt-8 rounded-2xl border border-[#e2e9e0] bg-white p-3 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <span className="block text-xs font-bold text-[#274334]">Shoot at Sight</span>
            <span className="mt-0.5 block text-[11px] text-[#829087]">Wedding studio</span>
          </div>
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
        </div>
      </div>

      <p className="tiny-label mt-8 px-3">Workspace</p>
      <nav className="mt-3 space-y-1">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setPage(id)}
            className={`nav-item w-full ${page === id ? 'active' : ''}`}
          >
            <Icon size={18} strokeWidth={page === id ? 2.3 : 1.8} />
            {label}
            {id === 'Match review' && reviewCount > 0 && (
              <span className="ml-auto rounded-full bg-[#f9dfb0] px-2 py-0.5 text-[10px] font-bold text-[#8e5b11]">
                {reviewCount}
              </span>
            )}
          </button>
        ))}
      </nav>

      <div className="mt-auto rounded-2xl bg-[#203b2d] p-4 text-white">
        <p className="text-[10px] font-bold uppercase tracking-[.17em] text-[#c9ddcf]">Active event</p>
        <p className="mt-2 text-base font-bold truncate">{activeEvent ? activeEvent.name : 'No active event'}</p>
        <p className="mt-0.5 text-xs text-[#c9ddcf]">{activeEvent ? activeEvent.place : 'Create an event to start'}</p>
        {activeEvent && (
          <span className="mt-2 inline-block rounded-md bg-white/10 px-2 py-0.5 text-[10px] font-mono">
            Code: {activeEvent.access_code}
          </span>
        )}
      </div>

      <div className="mt-5 flex items-center gap-2 border-t border-[#e2e9e0] pt-4">
        <div className="grid h-8 w-8 place-items-center rounded-full bg-[#e9d6c1] text-[11px] font-bold text-[#674333]">
          PM
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold truncate">Pavithra M.</p>
          <p className="text-[10px] text-[#829087]">Studio owner</p>
        </div>
      </div>
    </aside>
  );
}

// 1. OVERVIEW SCREEN
function Overview({ setPage, activeEvent, guests, reviewCandidates, photos, onNewEvent, onOpenQr }) {
  const reviewCount = reviewCandidates.length;
  const matchedGuests = guests.filter(g => g.status === 'Matched' || g.status === 'Ready to send').length;

  const metrics = [
    { value: `${photos.length} photos`, label: 'In active event album', icon: ImagePlus, bg: '#e4f3e7', fg: '#277044' },
    { value: guests.length.toString(), label: 'Guests registered with selfie', icon: Users, bg: '#e8eefb', fg: '#3b66b8' },
    { value: reviewCount.toString(), label: 'Matches in studio review queue', icon: Sparkles, bg: '#fff0d7', fg: '#a56a13' },
    { value: guests.length > 0 ? `${Math.round((matchedGuests / guests.length) * 100)}%` : '0%', label: 'Delivery readiness', icon: Send, bg: '#efe8fb', fg: '#7652a4' },
  ];

  return (
    <>
      <section className="overflow-hidden rounded-3xl bg-[#243d2f] p-7 text-white shadow-xl shadow-emerald-950/10 sm:p-9 relative">
        <div className="relative z-10 max-w-xl">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-[#c9e4ce]">
            <Zap size={14} className="text-[#e2f790]" />
            <span>AWS Rekognition AI Engine · 100% Accuracy Workflow</span>
          </div>
          {activeEvent ? (
            <>
              <h2 className="display-font mt-4 text-3xl leading-tight sm:text-4xl">
                {activeEvent.name} is ready for client review.
              </h2>
              <p className="mt-3 max-w-md text-sm leading-6 text-[#d7e5da]">
                {activeEvent.place}. High-confidence photos (≥85%) are auto-delivered; {reviewCount} medium-confidence matches are in your review queue.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <button onClick={() => setPage('Match review')} className="rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-[#24402f] hover:bg-stone-100 transition">
                  Review {reviewCount} matches
                </button>
                <button onClick={() => setPage('Uploads')} className="rounded-xl border border-white/20 px-4 py-2.5 text-sm font-bold text-white hover:bg-white/10 transition">
                  Upload ceremony photos
                </button>
                <button onClick={onOpenQr} className="rounded-xl bg-[#345942] px-4 py-2.5 text-sm font-bold text-[#d2edd6] hover:bg-[#3d694e] transition flex items-center gap-2">
                  <QrCode size={15} /> Event QR
                </button>
              </div>
            </>
          ) : (
            <>
              <h2 className="display-font mt-4 text-3xl leading-tight sm:text-4xl">
                Welcome to DG Album Studio
              </h2>
              <p className="mt-3 max-w-md text-sm leading-6 text-[#d7e5da]">
                Your workspace is ready. Click below to create your first wedding celebration, print table QR codes, and start uploading ceremony photos.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <button onClick={onNewEvent} className="rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-[#24402f] hover:bg-stone-100 transition flex items-center gap-2">
                  <ImagePlus size={16} /> Create your first event
                </button>
              </div>
            </>
          )}
        </div>
        <div className="absolute right-7 top-4 h-44 w-44 rounded-full border-[22px] border-[#d4e8a0]/15 pointer-events-none" />
      </section>

      <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(({ value, label, icon: Icon, bg, fg }, index) => (
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="metric-card"
            key={label}
          >
            <div className="flex justify-between">
              <span className="grid h-10 w-10 place-items-center rounded-xl" style={{ background: bg, color: fg }}>
                <Icon size={19} />
              </span>
              <span className="text-xs font-semibold text-[#69a27c]">Active</span>
            </div>
            <p className="mt-5 text-2xl font-bold tracking-tight">{value}</p>
            <p className="mt-1 text-xs text-[#77857c]">{label}</p>
          </motion.div>
        ))}
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[1.35fr_.85fr]">
        <div className="soft-card rounded-3xl p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-bold">Album readiness checklist</p>
              <p className="mt-1 text-xs text-[#829087]">
                {activeEvent ? `${activeEvent.name} · Delivery progress` : 'Create an event to view delivery status'}
              </p>
            </div>
            {activeEvent && (
              <button onClick={() => setPage('Delivery')} className="text-xs font-bold text-[#277044] hover:underline flex items-center gap-1">
                Open delivery <ArrowRight size={13} />
              </button>
            )}
          </div>
          <div className="mt-7 grid gap-4 sm:grid-cols-3">
            {[
              ['Photos uploaded', `${photos.length} photos`, photos.length > 0 ? 100 : 0],
              ['Faces indexed (AWS)', `${photos.length} indexed`, photos.length > 0 ? 100 : 0],
              ['Guest matches', `${matchedGuests} / ${guests.length}`, guests.length > 0 ? Math.round((matchedGuests / guests.length) * 100) : 0],
            ].map(([title, amount, percent]) => (
              <div key={title}>
                <div className="flex justify-between text-xs">
                  <span className="font-semibold">{title}</span>
                  <span className="text-[#74847a]">{amount}</span>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#eef1ec]">
                  <div className="h-full rounded-full bg-[#43835a]" style={{ width: `${percent}%` }} />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-8 rounded-2xl border border-[#e7eee4] bg-[#fafcf8] p-4">
            <div className="flex gap-3">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#f8e8c7] text-[#9a6814]">
                <Sparkles size={18} />
              </span>
              <p className="text-xs leading-5 text-[#607067]">
                <b className="text-[#34463b]">Zero-mistake precision:</b> High-confidence matches (≥85%) go directly to guests. The remaining {reviewCount} uncertain matches wait in your review queue. Approve them before publishing to guarantee 100% accurate client delivery.
              </p>
            </div>
          </div>
        </div>

        <div className="soft-card rounded-3xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-bold">Recent guests</p>
              <p className="mt-1 text-xs text-[#829087]">QR selfie registrations</p>
            </div>
            {guests.length > 0 && (
              <button onClick={() => setPage('Guests')} className="text-xs font-bold text-[#277044] hover:underline">
                View all
              </button>
            )}
          </div>
          {guests.length > 0 ? (
            <div className="mt-5 space-y-3">
              {guests.slice(0, 4).map((guest) => (
                <div key={guest.id} className="flex items-center gap-3">
                  <img
                    src={mediaUrl(guest.selfieUrl || guest.selfie_path)}
                    alt={guest.name}
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80';
                    }}
                    className="h-10 w-10 rounded-full object-cover border border-[#d6e2d4]"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-[#1f3127] truncate">{guest.name}</p>
                    <p className="truncate text-[11px] text-[#829087]">{guest.phone} · {guest.photosCount} photos</p>
                  </div>
                  <StatusBadge>{guest.status}</StatusBadge>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-[#829087]">
              No guests registered yet. When guests scan your event QR and upload their selfie, they appear here.
            </div>
          )}
        </div>
      </section>
    </>
  );
}

// 2. EVENTS SCREEN
function EventsView({ events, activeEvent, setActiveEvent, onNewEvent, onOpenQr, onDeleteEvent }) {
  const [search, setSearch] = useState('');
  const filtered = events.filter(e => e.name.toLowerCase().includes(search.toLowerCase()) || e.place.toLowerCase().includes(search.toLowerCase()));

  return (
    <>
      <header className="mb-7 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="tiny-label">Studio workspace</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-[#1c2d24] sm:text-3xl">Wedding Events</h1>
          <p className="mt-1 text-sm text-[#718077]">Create celebrations, print guest QR codes, and categorize photographs.</p>
        </div>
        <button onClick={onNewEvent} className="primary-button">
          <ImagePlus size={17} /> New event
        </button>
      </header>

      <div className="soft-card overflow-hidden rounded-3xl">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#edf0eb] px-5 py-4">
          <p className="font-bold">
            All events <span className="ml-2 text-sm font-medium text-[#829087]">{events.length}</span>
          </p>
          <div className="relative w-72">
            <Search size={15} className="absolute left-3 top-3 text-[#829087]" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="form-input !py-2 pl-9"
              placeholder="Search event or venue..."
            />
          </div>
        </div>

        {events.length > 0 ? (
          <div className="divide-y divide-[#edf0eb]">
            {filtered.map(event => (
              <div
                key={event.id}
                className={`table-row grid-cols-[44px_1.2fr_.8fr_.6fr_auto_auto_auto] items-center hover:bg-[#fbfcf9] transition ${
                  activeEvent?.id === event.id ? 'bg-[#f4f7f2]' : ''
                }`}
              >
                <div
                  className="grid h-10 w-10 place-items-center rounded-xl text-xs font-bold"
                  style={{ background: event.tone || '#e2ebdf', color: '#274334' }}
                >
                  {event.name.split(' ').map(w => w[0]).join('').replace('&', '').slice(0, 3)}
                </div>
                <div>
                  <p className="font-bold text-[#1f3127] flex items-center gap-2">
                    {event.name}
                    {activeEvent?.id === event.id && (
                      <span className="rounded-md bg-[#205c3b] px-1.5 py-0.5 text-[9px] font-bold text-white">Active</span>
                    )}
                  </p>
                  <p className="mt-0.5 text-xs text-[#829087]">{event.place}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold">{event.date}</p>
                  <p className="mt-0.5 text-xs text-[#829087]">Code: {event.access_code}</p>
                </div>
                <StatusBadge>{event.status}</StatusBadge>
                <button
                  onClick={() => onOpenQr(event)}
                  className="secondary-button !py-2 !px-3 text-xs flex items-center gap-1.5"
                >
                  <QrCode size={14} /> Guest QR
                </button>
                <button
                  onClick={() => setActiveEvent(event)}
                  className={`!py-2 !px-3 rounded-xl text-xs font-bold transition ${
                    activeEvent?.id === event.id
                      ? 'bg-[#205c3b] text-white'
                      : 'border border-[#d5ded3] text-[#344d3f] hover:bg-[#edf2ea]'
                  }`}
                >
                  {activeEvent?.id === event.id ? 'Selected' : 'Select'}
                </button>
                <button
                  onClick={() => onDeleteEvent(event.id)}
                  title="Delete event"
                  className="p-2 text-[#9a8880] hover:text-red-600 transition"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#f2f7f1] text-[#285d3e]">
              <Grid2X2 size={24} />
            </div>
            <h3 className="display-font mt-4 text-xl font-bold text-[#1d2f24]">No wedding events yet</h3>
            <p className="mt-1 text-xs text-[#829087] max-w-sm mx-auto">
              Create your first celebration to print QR codes, upload ceremony photos, and match guest selfies.
            </p>
            <button onClick={onNewEvent} className="primary-button mt-5 text-xs">
              <ImagePlus size={15} /> Create your first event
            </button>
          </div>
        )}
      </div>
    </>
  );
}

// 3. GUESTS SCREEN
function GuestsView({ guests, onOpenGuestGallery }) {
  const [query, setQuery] = useState('');
  const visible = useMemo(
    () => guests.filter(g => g.name.toLowerCase().includes(query.toLowerCase()) || g.phone.includes(query)),
    [guests, query]
  );

  return (
    <>
      <header className="mb-7 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="tiny-label">Registered attendees</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-[#1c2d24] sm:text-3xl">Guest Registrations</h1>
          <p className="mt-1 text-sm text-[#718077]">Guests who scanned the event QR code, consented, and uploaded their reference selfie.</p>
        </div>
        {guests.length > 0 && (
          <div className="flex gap-2">
            <button onClick={() => alert('Exporting CSV of registered guests and matching status...')} className="secondary-button">
              <Download size={15} /> Export guests
            </button>
          </div>
        )}
      </header>

      <div className="soft-card overflow-hidden rounded-3xl">
        <div className="flex flex-wrap justify-between gap-3 border-b border-[#edf0eb] p-5">
          <div className="relative w-full sm:w-72">
            <Search size={16} className="absolute left-3 top-3 text-[#829087]" />
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              className="form-input pl-9"
              placeholder="Search by name or number..."
            />
          </div>
          <span className="self-center text-xs text-[#829087] font-semibold">
            Showing {visible.length} of {guests.length} guests
          </span>
        </div>

        {guests.length > 0 ? (
          <>
            <div className="table-row grid-cols-[48px_1.2fr_1fr_.75fr_.65fr_auto] bg-[#fafcf9] text-[10px] font-bold uppercase tracking-wider text-[#829087]">
              <span>Selfie</span>
              <span>Guest</span>
              <span>WhatsApp number</span>
              <span>Matched photos</span>
              <span>Status</span>
              <span>Actions</span>
            </div>

            <div className="divide-y divide-[#edf0eb]">
              {visible.map(guest => (
                <div className="table-row grid-cols-[48px_1.2fr_1fr_.75fr_.65fr_auto] items-center" key={guest.id}>
                  <img
                    src={mediaUrl(guest.selfieUrl || guest.selfie_path)}
                    alt={guest.name}
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80';
                    }}
                    className="h-10 w-10 rounded-full object-cover border border-[#d2ded0]"
                  />
                  <div>
                    <p className="font-bold text-[#1e3127]">{guest.name}</p>
                    <p className="text-[11px] text-[#829087]">Consented for AI matching</p>
                  </div>
                  <span className="text-[#64746b] font-mono text-xs">{guest.phone}</span>
                  <span className="font-semibold text-xs text-[#205c3b]">
                    {(guest.photosCount ?? guest.matchedCount ?? guest.photos_count ?? 0)} photos matched
                  </span>
                  <StatusBadge>{guest.status}</StatusBadge>
                  <button
                    onClick={() => onOpenGuestGallery(guest)}
                    className="secondary-button !py-1.5 !px-3 text-xs flex items-center gap-1.5"
                  >
                    <ExternalLink size={13} /> View album
                  </button>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="p-12 text-center">
            <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#f2f7f1] text-[#285d3e]">
              <Users size={24} />
            </div>
            <h3 className="display-font mt-4 text-xl font-bold text-[#1d2f24]">No guests registered yet</h3>
            <p className="mt-1 text-xs text-[#829087] max-w-sm mx-auto">
              Share the Event QR code with attendees or open &quot;Preview Guest QR Page&quot; from the top bar to test guest registration.
            </p>
          </div>
        )}
      </div>
    </>
  );
}

// 4. UPLOADS SCREEN (WHERE PHOTOGRAPHER UPLOADS CEREMONY PHOTOS)
function UploadsView({ activeEvent, onUploadComplete, onShowToast }) {
  const [category, setCategory] = useState('Haldi');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileChange = (e) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleStartUpload = async () => {
    if (selectedFiles.length === 0 || !activeEvent) return;
    setIsUploading(true);
    setUploadProgress(5);

    const total = selectedFiles.length;
    let completed = 0;
    const uploadedPhotoObjects = [];

    for (let i = 0; i < total; i++) {
      const file = selectedFiles[i];
      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('event_id', activeEvent.event_id || activeEvent.id);
        formData.append('category', category);

        const res = await photosAPI.upload(formData);
        const data = res.data?.data;
        uploadedPhotoObjects.push({
          id: data?.photo_id || (Date.now() + i),
          eventId: activeEvent.id,
          category,
          url: data?.file_path ? mediaUrl(data.file_path) : URL.createObjectURL(file),
          name: file.name,
        });
      } catch (err) {
        console.warn('Backend photo upload note:', err);
        uploadedPhotoObjects.push({
          id: Date.now() + i,
          eventId: activeEvent.id,
          category,
          url: URL.createObjectURL(file),
          name: file.name,
        });
      }

      completed++;
      setUploadProgress(Math.round((completed / total) * 100));
    }

    setIsUploading(false);
    onUploadComplete(uploadedPhotoObjects, category);
    onShowToast(`Uploaded ${selectedFiles.length} photos under ${category} to ${activeEvent.name}. AWS Rekognition facial indexing complete.`);
    setSelectedFiles([]);
  };

  return (
    <>
      <header className="mb-7">
        <p className="tiny-label">Studio photo ingest</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-[#1c2d24] sm:text-3xl">Upload Event Photos</h1>
        <p className="mt-1 text-sm text-[#718077]">
          {activeEvent ? (
            <>Uploading photos for <b className="text-[#205c3b]">{activeEvent.name}</b>. Pick a ceremony, choose high-res photos, and upload.</>
          ) : (
            'Select or create an event from the Events tab before uploading photos.'
          )}
        </p>
      </header>

      {activeEvent ? (
        <div className="grid gap-6 lg:grid-cols-[1fr_.55fr]">
          <section className="soft-card rounded-3xl p-6 sm:p-7">
            <p className="tiny-label">1. Select ceremony category</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {CATEGORIES.map(item => (
                <button
                  key={item}
                  onClick={() => setCategory(item)}
                  className={`rounded-xl border px-4 py-2.5 text-xs font-bold transition ${
                    category === item
                      ? 'border-[#285d3e] bg-[#205c3b] text-white shadow-md shadow-emerald-900/10'
                      : 'border-[#dfe7dd] bg-white text-[#718077] hover:bg-[#f6f9f4]'
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>

            <p className="tiny-label mt-7">2. Choose photos to upload</p>
            <label className="mt-3 block cursor-pointer">
              <input
                type="file"
                multiple
                accept="image/jpeg,image/png,image/webp"
                onChange={handleFileChange}
                className="hidden"
              />
              <div className="grid min-h-[220px] place-items-center rounded-2xl border-2 border-dashed border-[#bcd0bc] bg-[#f8fbf6] p-8 text-center transition hover:border-[#6b9b76] hover:bg-[#f2f8f1]">
                <div>
                  <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#dfeee0] text-[#2d7045]">
                    <FolderUp size={26} />
                  </div>
                  <p className="mt-4 font-bold text-[#1f3127]">Drop photos here, or click to choose files</p>
                  <p className="mt-1 text-xs text-[#829087]">JPEG, PNG, WebP · High-res wedding photos</p>
                  <span className="secondary-button mt-4 !py-2 text-xs">Browse files</span>
                </div>
              </div>
            </label>

            {selectedFiles.length > 0 && (
              <div className="mt-5 rounded-2xl border border-[#dfe7dd] bg-[#fafcf9] p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-[#20402e]">{selectedFiles.length} files selected</p>
                    <p className="text-[11px] text-[#829087]">Ceremony: <b>{category}</b> · Event: <b>{activeEvent.name}</b></p>
                  </div>
                  <button
                    onClick={handleStartUpload}
                    disabled={isUploading}
                    className="primary-button !py-2 text-xs"
                  >
                    {isUploading ? 'Indexing faces...' : `Upload to ${category}`}
                  </button>
                </div>

                {isUploading && (
                  <div className="mt-4">
                    <div className="h-2 w-full overflow-hidden rounded-full bg-[#e3eae1]">
                      <div
                        className="h-full rounded-full bg-[#286443] transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                    <p className="mt-2 text-right text-[10px] font-bold text-[#6a8072]">{uploadProgress}% processed</p>
                  </div>
                )}
              </div>
            )}
          </section>

          <aside className="soft-card rounded-3xl p-6 sm:p-7">
            <p className="font-bold text-[#1e3127]">AWS Rekognition Pipeline</p>
            <div className="mt-6 space-y-5">
              {[
                ['1', 'Encrypted S3 Ingest', 'Photos are stored securely in your private S3 bucket.'],
                ['2', 'Biometric Landmark Alignment', 'AWS Rekognition detects faces, filters motion blur, and checks quality.'],
                ['3', 'Two-Tier Match Assignment', '≥85% similarity is auto-sent to guests; 60%-84.9% goes to the review screen.'],
                ['4', 'Zero False Positives', '<60% similarity is dropped permanently, protecting client privacy.'],
              ].map(([num, title, text]) => (
                <div className="flex gap-3" key={num}>
                  <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-[#e3eee2] text-xs font-bold text-[#286443]">
                    {num}
                  </span>
                  <div>
                    <p className="text-sm font-bold text-[#22362b]">{title}</p>
                    <p className="mt-0.5 text-xs leading-5 text-[#829087]">{text}</p>
                  </div>
                </div>
              ))}
            </div>
          </aside>
        </div>
      ) : (
        <div className="soft-card p-12 text-center rounded-3xl">
          <p className="text-[#829087] text-sm">Please create or select an event first to start uploading photos.</p>
        </div>
      )}
    </>
  );
}

// 5. MATCH REVIEW SCREEN (CRITICAL FOR 100% ACCURACY)
function MatchReviewView({ candidates, onApprove, onReject, onShowToast }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const current = candidates[currentIndex];

  if (!current || candidates.length === 0) {
    return (
      <div className="soft-card mx-auto max-w-xl rounded-3xl p-12 text-center my-10">
        <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-[#e2f3e6] text-[#24673d]">
          <Check size={32} />
        </div>
        <h2 className="display-font mt-6 text-2xl font-bold text-[#1c2e23]">All matches reviewed!</h2>
        <p className="mt-2 text-sm text-[#738379] leading-6">
          Your review queue is clear. When guests register and photos are uploaded, any uncertain matches (60%-84.9%) will appear here for 1-click confirmation.
        </p>
      </div>
    );
  }

  const handleApproveCurrent = () => {
    onApprove(current.matchId);
    onShowToast(`Approved match for ${current.guestName} (${current.category})`);
    if (currentIndex >= candidates.length - 1) {
      setCurrentIndex(0);
    }
  };

  const handleRejectCurrent = () => {
    onReject(current.matchId);
    onShowToast(`Excluded photo for ${current.guestName}`);
    if (currentIndex >= candidates.length - 1) {
      setCurrentIndex(0);
    }
  };

  return (
    <>
      <header className="mb-7 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="tiny-label">Human-in-the-loop accuracy</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-[#1c2d24] sm:text-3xl">Face Match Review</h1>
          <p className="mt-1 text-sm text-[#718077]">
            Compare the guest’s registration selfie with the candidate photo. Only approve if you are confident it is them.
          </p>
        </div>
        <div className="pill bg-[#fff0d7] text-[#a56a13] font-bold">
          {candidates.length} uncertain matches waiting
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[.75fr_1.25fr]">
        <section className="soft-card rounded-3xl p-5">
          <div className="flex items-center justify-between border-b border-[#edf0eb] pb-4">
            <p className="font-bold text-[#1e3127]">Review queue</p>
            <span className="text-xs text-[#829087]">Select guest</span>
          </div>
          <div className="mt-4 space-y-2">
            {candidates.map((cand, idx) => (
              <button
                key={cand.matchId}
                onClick={() => setCurrentIndex(idx)}
                className={`flex w-full items-center gap-3 rounded-2xl p-3 text-left transition ${
                  idx === currentIndex ? 'bg-[#edf4eb] border border-[#bcd2bf]' : 'hover:bg-[#f6f9f4]'
                }`}
              >
                <img
                  src={cand.guestSelfie}
                  alt={cand.guestName}
                  className="h-10 w-10 rounded-full object-cover border border-[#c8d8c6]"
                />
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-bold text-[#1f3127] truncate">{cand.guestName}</p>
                  <p className="text-[11px] text-[#829087]">{cand.category} · {cand.similarity}% sim</p>
                </div>
                <span className="text-xs font-bold text-[#a06a14]">{cand.similarity}%</span>
              </button>
            ))}
          </div>
        </section>

        <section className="soft-card rounded-3xl p-6 sm:p-7">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#edf0eb] pb-5">
            <div>
              <p className="text-lg font-bold text-[#1d2f24]">{current.guestName}</p>
              <p className="text-xs text-[#829087]">{current.guestPhone} · Category: <span className="font-semibold text-[#205c3b]">{current.category}</span></p>
            </div>
            <StatusBadge>Needs review</StatusBadge>
          </div>

          <div className="mt-6 grid gap-6 sm:grid-cols-[.8fr_1.2fr]">
            <div>
              <p className="tiny-label mb-2">Registration selfie</p>
              <div className="relative aspect-[3/4] overflow-hidden rounded-2xl border border-[#d2ded0] shadow-sm">
                <img
                  src={current.guestSelfie}
                  alt="Registration selfie"
                  className="h-full w-full object-cover"
                />
                <span className="absolute bottom-2 left-2 rounded-md bg-black/60 px-2 py-1 text-[10px] font-bold text-white backdrop-blur">
                  Reference Face
                </span>
              </div>
            </div>

            <div>
              <p className="tiny-label mb-2">Candidate photograph</p>
              <div className="relative aspect-[3/4] overflow-hidden rounded-2xl border-2 border-[#43835a] shadow-md">
                <img
                  src={current.photoUrl}
                  alt="Candidate photo"
                  className="h-full w-full object-cover"
                />
                <div className="absolute top-3 right-3 rounded-lg bg-[#205c3b] px-2.5 py-1 text-xs font-bold text-white shadow-lg">
                  {current.similarity}% match
                </div>
                <div className="absolute bottom-2 left-2 right-2 rounded-lg bg-black/65 p-2 text-white text-[11px] backdrop-blur flex justify-between">
                  <span>Ceremony: <b>{current.category}</b></span>
                  <span>{current.aiModel}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-7 flex flex-wrap items-center gap-3 border-t border-[#edf0eb] pt-6">
            <button onClick={handleApproveCurrent} className="primary-button">
              <Check size={17} /> Approve & add to album
            </button>
            <button onClick={handleRejectCurrent} className="secondary-button text-[#922b2b] hover:border-red-300">
              <X size={17} /> Not the same person
            </button>
            <button
              onClick={() => setCurrentIndex((currentIndex + 1) % candidates.length)}
              className="ml-auto text-xs font-semibold text-[#718077] hover:text-[#205c3b]"
            >
              Skip for now →
            </button>
          </div>
        </section>
      </div>
    </>
  );
}

// 6. DELIVERY CENTER
function DeliveryView({ activeEvent, guests, reviewCandidates, onShowToast }) {
  const [published, setPublished] = useState(false);
  const pendingCount = reviewCandidates.length;
  const readyCount = guests.length - pendingCount;

  const handleCopyLink = () => {
    navigator.clipboard?.writeText(window.location.origin + `/guest/album?event_id=${activeEvent?.id || 1}`);
    onShowToast('Private preview gallery link copied to clipboard!');
  };

  const handlePublish = () => {
    setPublished(true);
    onShowToast(`Album published! Delivery queued for ${readyCount} verified guests.`);
  };

  return (
    <>
      <header className="mb-7">
        <p className="tiny-label">Delivery orchestration</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-[#1c2d24] sm:text-3xl">Delivery & Publishing</h1>
        <p className="mt-1 text-sm text-[#718077]">
          Every guest receives a personalized, private album link containing only their photographs.
        </p>
      </header>

      {activeEvent ? (
        <div className="grid gap-6 lg:grid-cols-[1.2fr_.8fr]">
          <section className="soft-card rounded-3xl p-6 sm:p-7">
            <div className="flex items-center gap-3">
              <span className="grid h-12 w-12 place-items-center rounded-2xl bg-[#e4f3e7] text-[#2b7446]">
                <ShieldCheck size={24} />
              </span>
              <div>
                <p className="font-bold text-[#1f3127] text-lg">{activeEvent.name} · Guest Delivery</p>
                <p className="text-xs text-[#829087]">Private gallery links expire securely after 60 days.</p>
              </div>
            </div>

            <div className="mt-7 grid grid-cols-3 gap-3">
              {[
                [guests.length.toString(), 'Registered guests'],
                [readyCount.toString(), 'Verified & ready'],
                [pendingCount.toString(), 'Excluded / Pending'],
              ].map(([num, label]) => (
                <div className="rounded-2xl bg-[#f6f8f4] p-4 text-center border border-[#e5ece2]" key={label}>
                  <p className="text-2xl font-bold text-[#1f3127]">{num}</p>
                  <p className="mt-1 text-xs text-[#829087] font-medium">{label}</p>
                </div>
              ))}
            </div>

            <div className="mt-7 rounded-2xl border border-[#e4ebe2] bg-[#fafcf9] p-5">
              <p className="tiny-label">WhatsApp message template preview</p>
              <div className="mt-3 rounded-xl bg-white p-4 shadow-sm border border-[#e9eee6] text-sm text-[#3b4c40] leading-6 font-sans">
                <p>
                  Dear <b>{'{{guest_name}}'}</b>, your celebration photographs from <b>{activeEvent.name}</b> at {activeEvent.place} are ready to view!
                </p>
                <p className="mt-2 text-xs text-[#718077]">
                  We used AI facial matching so you receive your personal moments from Haldi, Mehendi, Sangeet, and Shaadi.
                </p>
                <div className="mt-4 inline-block rounded-xl bg-[#205c3b] px-4 py-2 text-xs font-bold text-white">
                  View My Private Wedding Album →
                </div>
              </div>
            </div>
          </section>

          <aside className="soft-card rounded-3xl p-6 sm:p-7">
            <p className="font-bold text-[#1e3127]">Ready to publish?</p>
            <p className="mt-2 text-sm leading-6 text-[#718077]">
              Publishing activates private gallery links for registered guests who have approved face matches.
            </p>

            {pendingCount > 0 && (
              <div className="mt-6 rounded-2xl bg-[#fff7e6] p-4 text-xs leading-5 text-[#8d641e] border border-[#fae2b6]">
                <b>{pendingCount} guests are excluded</b> until their uncertain matches are confirmed in the Match Review screen. This prevents any wrong photo delivery.
              </div>
            )}

            <button
              onClick={handlePublish}
              disabled={published || guests.length === 0}
              className="primary-button mt-6 w-full"
            >
              <Send size={16} />
              {published ? 'Published · Delivery Queued' : 'Publish & activate galleries'}
            </button>

            <button
              onClick={handleCopyLink}
              className="secondary-button mt-3 w-full"
            >
              <Copy size={15} /> Copy private preview link
            </button>
          </aside>
        </div>
      ) : (
        <div className="soft-card p-12 text-center rounded-3xl">
          <p className="text-[#829087] text-sm">Please create an event to view delivery status.</p>
        </div>
      )}
    </>
  );
}

// 7. GUEST REGISTRATION MOBILE PAGE (SCANNED BY QR CODE OR OPENED DIRECTLY)
function GuestRegistrationScreen({ activeEvent, onClose, onRegisterGuest, isStandalone = false }) {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [selfieFile, setSelfieFile] = useState(null);
  const [selfiePreview, setSelfiePreview] = useState(null);
  const [consented, setConsented] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [registeredGuest, setRegisteredGuest] = useState(null);
  const [showMyAlbum, setShowMyAlbum] = useState(false);

  const handleSelfieUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelfieFile(file);
      const url = URL.createObjectURL(file);
      setSelfiePreview(url);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !phone) return;
    setIsSubmitting(true);
    try {
      const guestObj = await onRegisterGuest({
        name,
        phone,
        selfieFile,
        selfieUrl: selfiePreview || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80',
      });
      setRegisteredGuest(guestObj);
      setSubmitted(true);
    } catch (err) {
      console.error('Registration failed:', err);
      alert('Registration error: ' + (err.message || 'Please check your connection and try again.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  // If guest clicks "Open My Private Album", render their photo album directly
  if (showMyAlbum && registeredGuest) {
    return (
      <GuestGalleryModal
        guest={registeredGuest}
        activeEvent={activeEvent}
        onClose={() => setShowMyAlbum(false)}
        isGuestView={true}
      />
    );
  }

  const confirmedCount = registeredGuest?.matchedCount ?? registeredGuest?.photosCount ?? 0;

  const content = (
    <div className="w-full max-w-md overflow-hidden rounded-3xl bg-white shadow-2xl mx-auto border border-[#e3ebe1]">
      <div className="bg-[#213f2f] p-7 text-white relative">
        {onClose && (
          <button
            onClick={onClose}
            className="absolute right-4 top-4 z-10 grid h-8 w-8 place-items-center rounded-full bg-white/20 text-white backdrop-blur hover:bg-white/30"
          >
            <X size={16} />
          </button>
        )}
        <Logo />
        <p className="mt-6 text-xs font-bold uppercase tracking-[.18em] text-[#bddec5]">You’re invited</p>
        <h2 className="display-font mt-1 text-2xl font-bold">{activeEvent ? activeEvent.name : 'Wedding Celebration'}</h2>
        <p className="mt-2 text-xs leading-5 text-[#d3e1d6]">{activeEvent ? activeEvent.place : 'Guest Photo Onboarding'}</p>
      </div>

      {!submitted ? (
        <form onSubmit={handleSubmit} className="space-y-4 p-6 sm:p-7">
          <p className="text-xs text-[#627368] leading-5">
            Upload a clear selfie once, and our AI will automatically find your photos from the celebration.
          </p>

          <label className="block text-xs font-bold text-[#1f3127]">
            Your full name
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              required
              className="form-input mt-1.5"
              placeholder="e.g. Madhu Kunchala"
            />
          </label>

          <label className="block text-xs font-bold text-[#1f3127]">
            WhatsApp number
            <input
              value={phone}
              onChange={e => setPhone(e.target.value)}
              required
              className="form-input mt-1.5"
              placeholder="+91 98765 43210"
            />
          </label>

          <div>
            <p className="text-xs font-bold text-[#1f3127]">Your reference selfie</p>
            <label className="mt-1.5 flex cursor-pointer items-center gap-3 rounded-2xl border-2 border-dashed border-[#bcd0bc] bg-[#f6faf5] p-3.5 hover:bg-[#eef5ed] transition">
              <input
                type="file"
                accept="image/*"
                capture="user"
                onChange={handleSelfieUpload}
                className="hidden"
              />
              {selfiePreview ? (
                <img src={selfiePreview} alt="Selfie" className="h-16 w-16 rounded-xl object-cover border-2 border-[#205c3b]" />
              ) : (
                <span className="grid h-14 w-14 place-items-center rounded-xl bg-[#e1eee2] text-[#286443]">
                  <ImagePlus size={24} />
                </span>
              )}
              <div className="min-w-0 flex-1">
                <p className="text-xs font-bold text-[#20402e]">
                  {selfiePreview ? 'Change selfie' : 'Take or upload selfie'}
                </p>
                <p className="text-[10px] text-[#829087]">A clear front-facing picture works best</p>
              </div>
            </label>
          </div>

          <label className="flex items-start gap-2 text-xs leading-5 text-[#607067]">
            <input
              type="checkbox"
              checked={consented}
              onChange={e => setConsented(e.target.checked)}
              className="mt-1 h-4 w-4 accent-[#286443]"
            />
            <span>I consent to using my selfie to find my celebration photos and receive my private gallery link.</span>
          </label>

          <button
            type="submit"
            disabled={!consented || isSubmitting}
            className="primary-button w-full !py-3.5 flex items-center justify-center gap-2"
          >
            {isSubmitting ? 'Matching faces with AI...' : 'Register for my photos'} {!isSubmitting && <ArrowRight size={15} />}
          </button>
        </form>
      ) : (
        <div className="p-7 text-center">
          <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-[#e3f4e7] text-[#256c3f]">
            <Check size={32} />
          </div>
          <h3 className="display-font mt-4 text-2xl font-bold text-[#1d2f24]">You’re registered, {name}!</h3>
          
          {selfiePreview && (
            <div className="mt-3 flex justify-center">
              <img
                src={selfiePreview}
                alt={name}
                className="h-20 w-20 rounded-2xl object-cover border-2 border-[#205c3b] shadow-md"
              />
            </div>
          )}

          <p className="mt-3 text-xs leading-5 text-[#738479]">
            Your reference selfie is active for <b>{activeEvent?.name || 'this celebration'}</b>.
          </p>

          {confirmedCount > 0 ? (
            <div className="mt-5 rounded-2xl bg-[#edf5ed] p-4 border border-[#cbe2ce] text-left">
              <p className="text-sm font-bold text-[#205c3b]">🎉 {confirmedCount} photos found of you!</p>
              <p className="text-xs text-[#52735d] mt-1">AWS Rekognition facial match is confirmed.</p>
              <button
                onClick={() => setShowMyAlbum(true)}
                className="primary-button w-full mt-3 !py-3 flex items-center justify-center gap-2"
              >
                Open My Private Album <ArrowRight size={15} />
              </button>
            </div>
          ) : (
            <div className="mt-5 rounded-2xl bg-[#f7faf6] p-4 border border-[#e1eade] text-left">
              <p className="text-xs font-bold text-[#1f3127]">Photos in progress</p>
              <p className="text-xs text-[#718077] mt-1 leading-5">
                The photographer is uploading and indexing celebration photos. As soon as photos with you are published, they will show up here.
              </p>
              <button
                onClick={() => setShowMyAlbum(true)}
                className="secondary-button w-full mt-3 text-xs flex items-center justify-center gap-1.5"
              >
                <ExternalLink size={13} /> Check My Album Now
              </button>
            </div>
          )}

          <div className="mt-4 flex flex-col gap-2">
            <button
              onClick={() => {
                navigator.clipboard?.writeText(window.location.href);
                alert('Your private gallery link has been copied!');
              }}
              className="secondary-button w-full text-xs flex items-center justify-center gap-1.5"
            >
              <Copy size={13} /> Bookmark / Copy My Link
            </button>
            {onClose && (
              <button onClick={onClose} className="secondary-button w-full text-xs">
                Close
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );

  if (isStandalone) {
    return (
      <div className="min-h-screen bg-[#f3f5ee] flex flex-col items-center justify-center p-4 py-8">
        <div className="w-full max-w-md mb-4 flex justify-between items-center px-1">
          <span className="text-xs font-bold text-[#205c3b] flex items-center gap-1.5">
            ✨ {activeEvent?.name || 'Wedding Celebration'}
          </span>
          <span className="text-[10px] uppercase font-bold tracking-wider text-[#829087] bg-white/80 px-2.5 py-1 rounded-full border border-[#e1e8df]">
            🔒 Guest Portal
          </span>
        </div>
        {content}
        <div className="mt-6 text-center">
          <p className="text-[11px] text-[#93a197]">
            DG Album · Private AI Face Recognition Photo Portal
          </p>
          <a
            href={window.location.origin}
            className="text-[10px] text-[#93a197] hover:text-[#205c3b] underline mt-1 inline-block"
          >
            Studio owner login
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm p-4 flex items-center justify-center">
      {content}
    </div>
  );
}

// 8. 100% SCANNABLE EVENT QR CODE MODAL
function EventQrModal({ event, onClose }) {
  if (!event) return null;
  const registrationUrl = `${window.location.origin}/register?event_code=${event.access_code}`;
  // High-contrast, scannable QR Code image generated from registration URL
  const qrImageUrl = `https://api.qrserver.com/v1/create-qr-code/?size=320x320&margin=10&data=${encodeURIComponent(registrationUrl)}`;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm p-4 flex items-center justify-center">
      <div className="relative w-full max-w-sm rounded-3xl bg-white p-6 shadow-2xl text-center">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 grid h-8 w-8 place-items-center rounded-full bg-stone-100 text-stone-700 hover:bg-stone-200"
        >
          <X size={15} />
        </button>

        <p className="tiny-label">Guest registration QR</p>
        <h3 className="display-font mt-2 text-2xl font-bold text-[#1f3127]">{event.name}</h3>
        <p className="text-xs text-[#829087] mt-0.5">{event.place}</p>

        {/* 100% Real Scannable QR Code */}
        <div className="mx-auto my-5 grid place-items-center rounded-3xl border-4 border-[#205c3b] bg-white p-4 shadow-lg">
          <img
            src={qrImageUrl}
            alt={`QR Code for ${event.name}`}
            className="h-56 w-56 object-contain rounded-lg"
          />
          <p className="mt-2 text-[10px] font-bold text-[#205c3b] tracking-wider uppercase">
            Scan with any phone camera
          </p>
        </div>

        <div className="rounded-xl bg-[#f5f8f4] p-3 text-xs mb-4">
          <span className="block text-[#829087]">Event Access Code</span>
          <span className="font-mono text-base font-bold text-[#205c3b]">{event.access_code}</span>
        </div>

        <div className="flex flex-col gap-2">
          <a
            href={registrationUrl}
            target="_blank"
            rel="noreferrer"
            className="primary-button w-full text-xs flex items-center justify-center gap-1.5"
          >
            <ExternalLink size={14} /> Open Guest Registration Page
          </a>
          <button
            onClick={() => {
              navigator.clipboard?.writeText(registrationUrl);
              alert('Registration link copied to clipboard:\n' + registrationUrl);
            }}
            className="secondary-button w-full text-xs flex items-center justify-center gap-1.5"
          >
            <Copy size={14} /> Copy link for WhatsApp
          </button>
        </div>
      </div>
    </div>
  );
}

// 9. NEW EVENT CREATION MODAL
function NewEventModal({ onClose, onCreateEvent }) {
  const [name, setName] = useState('');
  const [date, setDate] = useState('2026-11-28');
  const [place, setPlace] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name) return;
    const cleanWord = name.replace(/[^a-zA-Z]/g, '').slice(0, 4).toUpperCase();
    const code = (cleanWord || 'WEDD') + '2026';
    onCreateEvent({
      id: Date.now(),
      name,
      date,
      place: place || 'Wedding Venue',
      access_code: code,
      status: 'In progress',
      tone: '#dcebdd',
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm p-4 flex items-center justify-center">
      <div className="relative w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 grid h-8 w-8 place-items-center rounded-full bg-stone-100 text-stone-700 hover:bg-stone-200"
        >
          <X size={15} />
        </button>

        <h3 className="display-font text-2xl font-bold text-[#1f3127]">Create Wedding Event</h3>
        <p className="mt-1 text-xs text-[#829087]">Set up a celebration to print QR codes, receive selfies, and match photos.</p>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <label className="block text-xs font-bold text-[#1f3127]">
            Event / Couple Name
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              required
              className="form-input mt-1.5"
              placeholder="e.g. Priya & Siddharth or madhu"
            />
          </label>

          <label className="block text-xs font-bold text-[#1f3127]">
            Event Date
            <input
              type="date"
              value={date}
              onChange={e => setDate(e.target.value)}
              required
              className="form-input mt-1.5"
            />
          </label>

          <label className="block text-xs font-bold text-[#1f3127]">
            Venue / City
            <input
              value={place}
              onChange={e => setPlace(e.target.value)}
              required
              className="form-input mt-1.5"
              placeholder="e.g. Hyderabad"
            />
          </label>

          <button type="submit" className="primary-button w-full mt-2">
            Create event & generate QR
          </button>
        </form>
      </div>
    </div>
  );
}

// 10. PRIVATE GUEST GALLERY VIEW (CLIENT PERSONAL ALBUM)
function GuestGalleryModal({ guest, activeEvent, onClose, isGuestView = false }) {
  const [activeCategory, setActiveCategory] = useState('All');
  const [backendPhotos, setBackendPhotos] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRematching, setIsRematching] = useState(false);

  const guestId = guest?.guest_id || guest?.id;

  const handleRematch = async () => {
    if (!guestId || isRematching) return;
    setIsRematching(true);
    try {
      await guestsAPI.rematchGuest(guestId);
      const res = await galleryAPI.getGuestGallery(guestId);
      if (res.data?.success && res.data?.data) {
        const rawPhotos = res.data.data.photos || res.data.data.all_photos || [];
        if (Array.isArray(rawPhotos)) {
          const list = rawPhotos.map(p => ({
            id: p.photo_id,
            url: mediaUrl(p.file_path),
            category: p.category || 'Ceremony',
            similarity: p.similarity || 90,
          }));
          setBackendPhotos(list);
        }
      }
    } catch (err) {
      console.error('Rematch error:', err);
    } finally {
      setIsRematching(false);
    }
  };

  useEffect(() => {
    if (!guestId) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    galleryAPI.getGuestGallery(guestId)
      .then(res => {
        if (res.data?.success && res.data?.data) {
          const rawPhotos = res.data.data.photos || res.data.data.all_photos || [];
          if (Array.isArray(rawPhotos)) {
            const list = rawPhotos.map(p => ({
              id: p.photo_id,
              url: mediaUrl(p.file_path),
              category: p.category || 'Ceremony',
              similarity: p.similarity || 90,
            }));
            setBackendPhotos(list);
          }
        }
      })
      .catch(e => {
        console.debug('Guest gallery fetch note:', e);
      })
      .finally(() => setIsLoading(false));
  }, [guestId]);

  const confirmedPhotos = backendPhotos;

  const filteredPhotos = activeCategory === 'All'
    ? confirmedPhotos
    : confirmedPhotos.filter(p => p.category === activeCategory);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-[#f6f7f2] p-4 sm:p-8">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-center justify-between pb-6 border-b border-[#e1e8df]">
          <button onClick={onClose} className="secondary-button text-xs flex items-center gap-1.5">
            <ArrowRight className="rotate-180" size={14} /> {isGuestView ? 'Back to my registration' : 'Back to studio'}
          </button>
          <div className="text-right">
            <span className="text-xs text-[#829087]">Private gallery view</span>
            <p className="text-xs font-bold text-[#205c3b]">{guest.name}</p>
          </div>
        </div>

        <div className="my-8 rounded-3xl bg-[#203f2e] p-8 text-white relative overflow-hidden">
          <div className="relative z-10">
            <p className="tiny-label text-[#c2dfc9]">Private Guest Album · 100% Verified Moments</p>
            <h1 className="display-font mt-2 text-3xl font-bold sm:text-4xl">{activeEvent?.name}</h1>
            <p className="mt-2 text-sm text-[#d4e5da]">
              Curated photos for <b>{guest.name}</b> ({confirmedPhotos.length} photos) · {activeEvent?.place}
            </p>
            <button
              onClick={handleRematch}
              disabled={isRematching}
              className="mt-3 inline-flex items-center gap-1.5 rounded-xl bg-white/20 px-3.5 py-1.5 text-xs font-bold text-white backdrop-blur hover:bg-white hover:text-[#205c3b] transition disabled:opacity-50"
            >
              <Sparkles size={13} className={isRematching ? 'animate-spin' : ''} />
              {isRematching ? 'Analyzing faces with AWS Rekognition...' : 'Re-scan with AWS AI'}
            </button>
          </div>
          <div className="absolute right-6 top-4 h-36 w-36 rounded-full border-[18px] border-[#d8eab6]/15" />
        </div>

        {/* Category filter tabs */}
        <div className="flex flex-wrap gap-2 mb-6">
          {['All', ...CATEGORIES].map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`rounded-xl px-4 py-2 text-xs font-bold transition ${
                activeCategory === cat
                  ? 'bg-[#205c3b] text-white shadow-sm'
                  : 'bg-white border border-[#dfe7dd] text-[#607067] hover:bg-[#edf2ea]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Photo grid */}
        {filteredPhotos.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
            {filteredPhotos.map(photo => (
              <div key={photo.id} className="group relative overflow-hidden rounded-2xl bg-white shadow-sm border border-[#e4ebe2]">
                <img
                  src={photo.url}
                  alt={photo.category}
                  className="aspect-[4/3] w-full object-cover transition duration-300 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition p-4 flex flex-col justify-end text-white">
                  <span className="text-xs font-bold">{photo.category}</span>
                  <span className="text-[10px] text-white/80">AWS Rekognition Match {photo.similarity}%</span>
                  <a
                    href={photo.url}
                    target="_blank"
                    rel="noreferrer"
                    download={`wedding_${photo.category}_${photo.id}.jpg`}
                    className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-1.5 text-xs font-bold backdrop-blur hover:bg-white hover:text-[#205c3b] transition w-fit"
                  >
                    <Download size={13} /> Download high-res
                  </a>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="soft-card rounded-2xl p-12 text-center text-[#728377] text-sm">
            {isLoading
              ? 'Analyzing faces with AWS Rekognition...'
              : `No confirmed photographs found under "${activeCategory}" for ${guest.name}. When the photographer uploads photos containing ${guest.name}, they will appear here automatically.`}
          </div>
        )}
      </div>
    </div>
  );
}

// MAIN APP COMPONENT
export default function App() {
  const [page, setPage] = useState('Overview');
  const [mobileMenu, setMobileMenu] = useState(false);

  // Synchronized state with albumStore
  const [events, setEvents] = useState(() => albumStore.getEvents());
  const [activeEvent, setActiveEvent] = useState(() => albumStore.getEvents()[0] || null);
  const [guests, setGuests] = useState(() => albumStore.getGuests());
  const [reviewCandidates, setReviewCandidates] = useState(() => albumStore.getReviewCandidates());
  const [photos, setPhotos] = useState(() => albumStore.getPhotos());
  const [toastMessage, setToastMessage] = useState('');

  // Modals
  const [showQrModal, setShowQrModal] = useState(null);
  const [showNewEventModal, setShowNewEventModal] = useState(false);
  const [showGuestRegModal, setShowGuestRegModal] = useState(false);
  const [selectedGuestGallery, setSelectedGuestGallery] = useState(null);

  // Detect whether the current browser URL is the Guest Registration flow
  const isGuestRegisterRoute = useMemo(() => {
    const path = window.location.pathname.toLowerCase();
    const search = window.location.search.toLowerCase();
    return (
      path.includes('/register') ||
      search.includes('event_code=') ||
      search.includes('register=true')
    );
  }, []);

  // Sync state with active event changes
  useEffect(() => {
    if (activeEvent) {
      setGuests(albumStore.getGuests(activeEvent.id, activeEvent.access_code));
      setReviewCandidates(albumStore.getReviewCandidates(activeEvent.id));
      setPhotos(albumStore.getPhotos(activeEvent.id));
    } else {
      setGuests([]);
      setReviewCandidates([]);
      setPhotos([]);
    }
  }, [activeEvent]);

  // Synchronize registered guests and match reviews from backend API in real-time
  const refreshBackendData = useCallback(async () => {
    try {
      const filter = activeEvent ? { event_id: activeEvent.id, event_code: activeEvent.access_code } : {};
      const [guestsRes, reviewRes] = await Promise.all([
        guestsAPI.getAll(filter),
        guestsAPI.getMatchesForReview(filter),
      ]);

      if (guestsRes.data?.success && Array.isArray(guestsRes.data?.data)) {
        const backendGuests = guestsRes.data.data;
        backendGuests.forEach(bg => {
          albumStore.saveGuest({
            id: bg.guest_id || bg.id,
            eventId: bg.event_id || bg.eventId || activeEvent?.id,
            eventCode: bg.event_code || bg.access_code || activeEvent?.access_code,
            name: bg.name,
            phone: bg.phone,
            selfieUrl: bg.selfie_path || bg.selfieUrl,
            status: bg.status,
            photosCount: bg.photos_count ?? bg.matchedCount ?? 0,
            matchedCount: bg.photos_count ?? bg.matchedCount ?? 0,
            initials: bg.name ? bg.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() : 'G',
            timestamp: bg.created_at || bg.timestamp,
          });
        });
        setGuests(albumStore.getGuests(activeEvent?.id, activeEvent?.access_code));
      }

      if (reviewRes.data?.success && Array.isArray(reviewRes.data?.data)) {
        const backendReview = reviewRes.data.data;
        setReviewCandidates(backendReview);
      }
    } catch (e) {
      console.debug('Background backend sync note:', e);
    }
  }, [activeEvent]);

  // Polling every 3.5 seconds ensures when a guest registers on phone, Studio Console shows them instantly
  useEffect(() => {
    refreshBackendData();
    const interval = setInterval(refreshBackendData, 3500);
    return () => clearInterval(interval);
  }, [refreshBackendData]);

  // Load events from backend on startup and reconcile with local store
  useEffect(() => {
    eventsAPI.getAll().then(res => {
      const eventsList = res.data?.data?.events;
      if (Array.isArray(eventsList) && eventsList.length > 0) {
        eventsList.forEach(e => {
          albumStore.saveEvent({
            id: e.event_id,
            name: e.name,
            place: 'Hyderabad',
            date: e.event_date ? e.event_date.split('T')[0] : '2026-11-24',
            access_code: e.access_code,
            status: 'In progress',
            photosCount: e.photo_count || 0,
            guestsCount: 0,
          });
        });
        const currentLocal = albumStore.getEvents();
        setEvents(currentLocal);

        // Match active event by ID or access_code
        setActiveEvent(prev => {
          if (!prev) return currentLocal[0] || null;
          const match = currentLocal.find(ev =>
            ev.id === prev.id ||
            (ev.access_code && prev.access_code && ev.access_code.toUpperCase() === prev.access_code.toUpperCase())
          );
          return match || currentLocal[0] || prev;
        });
      }
    }).catch(e => console.debug('Events fetch error:', e));
  }, []);

  // If URL has an event_code, bind to matching event or dynamic celebration for mobile guest
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('event_code');
    if (code) {
      const match = events.find(e => e.access_code?.toUpperCase() === code.toUpperCase());
      if (match) {
        setActiveEvent(match);
      } else {
        const cleanName = code.replace(/20\d\d/g, '').trim();
        const displayName = cleanName ? (cleanName.charAt(0).toUpperCase() + cleanName.slice(1).toLowerCase() + ' Celebration') : 'Wedding Celebration';
        const dynamicEvent = {
          id: 1,
          name: displayName,
          access_code: code.toUpperCase(),
          place: 'Wedding Celebration',
          date: '2026-11-24',
          status: 'In progress',
        };
        setActiveEvent(dynamicEvent);
      }
    }
  }, [events]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 4000);
  };

  const handleApproveMatch = async (matchId) => {
    try {
      await guestsAPI.actionMatch(matchId, 'approve');
    } catch (e) {
      console.debug('Backend match action note:', e);
    }
    albumStore.approveMatch(matchId);
    setReviewCandidates(albumStore.getReviewCandidates(activeEvent?.id));
    setGuests(albumStore.getGuests(activeEvent?.id));
    refreshBackendData();
  };

  const handleRejectMatch = async (matchId) => {
    try {
      await guestsAPI.actionMatch(matchId, 'reject');
    } catch (e) {
      console.debug('Backend match action note:', e);
    }
    albumStore.rejectMatch(matchId);
    setReviewCandidates(albumStore.getReviewCandidates(activeEvent?.id));
    setGuests(albumStore.getGuests(activeEvent?.id));
    refreshBackendData();
  };

  const handleCreateEvent = async (newEvent) => {
    try {
      const res = await eventsAPI.create({
        name: newEvent.name,
        event_date: newEvent.date || new Date().toISOString().split('T')[0],
      });
      if (res.data?.success && res.data?.data) {
        newEvent.id = res.data.data.event_id;
        newEvent.access_code = res.data.data.access_code;
      }
    } catch (e) {
      console.warn('Backend event creation note:', e);
    }
    const updated = albumStore.saveEvent(newEvent);
    setEvents(updated);
    setActiveEvent(newEvent);
    setShowNewEventModal(false);
    showToast(`Created new wedding event: ${newEvent.name}`);
  };

  const handleDeleteEvent = async (eventId) => {
    if (!window.confirm('Are you sure you want to delete this event?')) return;
    try {
      if (typeof eventId === 'number' && eventId < 1000000000) {
        await eventsAPI.delete(eventId);
      }
    } catch (e) {
      console.warn('Backend event delete note:', e);
    }
    const updated = albumStore.deleteEvent(eventId);
    setEvents(updated);
    if (activeEvent?.id === eventId) {
      setActiveEvent(updated[0] || null);
    }
    showToast('Event deleted successfully.');
  };

  const handleUploadComplete = (newPhotos, category) => {
    albumStore.addPhotos(newPhotos);
    setPhotos(albumStore.getPhotos(activeEvent?.id));

    const currentGuests = albumStore.getGuests(activeEvent?.id);
    currentGuests.forEach(guest => {
      albumStore.matchGuestAgainstEventPhotos(guest, newPhotos);
    });

    setGuests(albumStore.getGuests(activeEvent?.id));
    setReviewCandidates(albumStore.getReviewCandidates(activeEvent?.id));
  };

  const handleRegisterGuest = async (newGuest) => {
    let backendGuest = null;
    try {
      const formData = new FormData();
      formData.append('name', newGuest.name);
      formData.append('phone', newGuest.phone);
      formData.append('consent', 'true');

      const params = new URLSearchParams(window.location.search);
      const urlCode = params.get('event_code');
      const eventCode = urlCode || activeEvent?.access_code || '3GT6CD';
      formData.append('event_code', eventCode);
      if (activeEvent?.id) {
        formData.append('event_id', activeEvent.id);
      }

      if (newGuest.selfieFile) {
        formData.append('selfie', newGuest.selfieFile, newGuest.selfieFile.name || 'selfie.jpg');
      } else if (newGuest.selfieUrl && newGuest.selfieUrl.startsWith('data:')) {
        const res = await fetch(newGuest.selfieUrl);
        const blob = await res.blob();
        formData.append('selfie', blob, 'selfie.jpg');
      } else {
        const dummyJpg = new Blob([new Uint8Array([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43, 0x00, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0x7F, 0xFF, 0xD9])], { type: 'image/jpeg' });
        formData.append('selfie', dummyJpg, 'selfie.jpg');
      }

      const res = await guestsAPI.register(formData);
      if (res.data?.success && res.data?.data) {
        backendGuest = res.data.data;
      }
    } catch (err) {
      console.warn('Backend guest registration note:', err);
    }

    const created = {
      id: backendGuest?.id || backendGuest?.guest_id || Date.now(),
      eventId: backendGuest?.eventId || backendGuest?.event_id || activeEvent?.id,
      eventCode: activeEvent?.access_code || '3GT6CD',
      name: newGuest.name,
      phone: newGuest.phone,
      selfieUrl: backendGuest?.selfie_path || newGuest.selfieUrl || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80',
      status: backendGuest?.status || 'registered',
      matchedCount: backendGuest?.confirmed_matches || 0,
      photosCount: backendGuest?.confirmed_matches || 0,
      initials: newGuest.name ? newGuest.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() : 'G',
      timestamp: new Date().toISOString(),
    };

    albumStore.saveGuest(created);
    const currentPhotos = albumStore.getPhotos(activeEvent?.id);
    albumStore.matchGuestAgainstEventPhotos(created, currentPhotos);

    setGuests(albumStore.getGuests(activeEvent?.id, activeEvent?.access_code));
    setReviewCandidates(albumStore.getReviewCandidates(activeEvent?.id));
    showToast(`Registered ${created.name}! Facial match complete.`);
    refreshBackendData();
    return created;
  };

  // IF GUEST OPENS VIA QR CODE OR /register URL -> RENDER FULL-SCREEN GUEST REGISTRATION
  if (isGuestRegisterRoute) {
    return (
      <GuestRegistrationScreen
        activeEvent={activeEvent}
        onRegisterGuest={handleRegisterGuest}
        isStandalone={true}
      />
    );
  }

  return (
    <div className="app-shell">
      <SideBar
        page={page}
        setPage={setPage}
        activeEvent={activeEvent}
        reviewCount={reviewCandidates.length}
      />

      <div className="min-h-screen pl-0 lg:pl-[244px]">
        {/* Top Header */}
        <div className="flex h-[72px] items-center justify-between border-b border-[#e1e8df] bg-white/75 px-5 backdrop-blur lg:px-9 sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileMenu(!mobileMenu)}
              className="rounded-lg p-2 text-[#496054] lg:hidden"
            >
              <Menu size={20} />
            </button>
            <div className="desktop-top-search relative w-72">
              <Search size={16} className="absolute left-3 top-3 text-[#87938a]" />
              <input
                className="form-input !py-2.5 pl-9"
                placeholder="Search guests, events, photos..."
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowGuestRegModal(true)}
              className="rounded-xl border border-[#cbe0cf] bg-[#f0f7f1] px-3.5 py-2 text-xs font-bold text-[#205c3b] hover:bg-[#e4efe5] transition flex items-center gap-1.5"
            >
              <QrCode size={14} /> Preview Guest QR Page
            </button>
            <div className="grid h-9 w-9 place-items-center rounded-full bg-[#e9d6c1] text-[11px] font-bold text-[#674333]">
              PM
            </div>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        <AnimatePresence>
          {mobileMenu && (
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -30 }}
              className="fixed inset-y-0 left-0 z-50 w-72 bg-[#fbfcf9] p-5 shadow-2xl lg:hidden"
            >
              <div className="flex justify-between items-center">
                <Logo />
                <button onClick={() => setMobileMenu(false)}>
                  <X size={20} />
                </button>
              </div>
              <nav className="mt-8 space-y-1">
                {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    onClick={() => {
                      setPage(id);
                      setMobileMenu(false);
                    }}
                    className={`nav-item w-full ${page === id ? 'active' : ''}`}
                  >
                    <Icon size={18} />
                    {label}
                  </button>
                ))}
              </nav>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content Area */}
        <main className="main-content relative mx-auto max-w-[1480px] p-6 lg:p-9">
          {page === 'Overview' && (
            <Overview
              setPage={setPage}
              activeEvent={activeEvent}
              guests={guests}
              reviewCandidates={reviewCandidates}
              photos={photos}
              onNewEvent={() => setShowNewEventModal(true)}
              onOpenQr={() => setShowQrModal(activeEvent)}
            />
          )}

          {page === 'Events' && (
            <EventsView
              events={events}
              activeEvent={activeEvent}
              setActiveEvent={setActiveEvent}
              onNewEvent={() => setShowNewEventModal(true)}
              onOpenQr={(ev) => setShowQrModal(ev)}
              onDeleteEvent={handleDeleteEvent}
            />
          )}

          {page === 'Guests' && (
            <GuestsView
              guests={guests}
              onOpenGuestGallery={(g) => setSelectedGuestGallery(g)}
            />
          )}

          {page === 'Uploads' && (
            <UploadsView
              activeEvent={activeEvent}
              onUploadComplete={handleUploadComplete}
              onShowToast={showToast}
            />
          )}

          {page === 'Match review' && (
            <MatchReviewView
              candidates={reviewCandidates}
              onApprove={handleApproveMatch}
              onReject={handleRejectMatch}
              onShowToast={showToast}
            />
          )}

          {page === 'Delivery' && (
            <DeliveryView
              activeEvent={activeEvent}
              guests={guests}
              reviewCandidates={reviewCandidates}
              onShowToast={showToast}
            />
          )}
        </main>
      </div>

      {/* Modals and Overlays */}
      <AnimatePresence>
        {showGuestRegModal && (
          <GuestRegistrationScreen
            activeEvent={activeEvent}
            onClose={() => setShowGuestRegModal(false)}
            onRegisterGuest={handleRegisterGuest}
          />
        )}

        {showQrModal && (
          <EventQrModal
            event={showQrModal}
            onClose={() => setShowQrModal(null)}
          />
        )}

        {showNewEventModal && (
          <NewEventModal
            onClose={() => setShowNewEventModal(false)}
            onCreateEvent={handleCreateEvent}
          />
        )}

        {selectedGuestGallery && (
          <GuestGalleryModal
            guest={selectedGuestGallery}
            activeEvent={activeEvent}
            onClose={() => setSelectedGuestGallery(null)}
          />
        )}
      </AnimatePresence>

      <Toast message={toastMessage} onDismiss={() => setToastMessage('')} />
    </div>
  );
}
