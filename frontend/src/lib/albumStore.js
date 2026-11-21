/**
 * DG Album Persistent Storage & Face Matching Engine
 * 
 * Clean production store - no dummy/sample seed data.
 * All events, guests, ceremony photos, and match reviews are 100% real user data.
 */

const DB_PREFIX = 'dg_album_clean_v4_';

class AlbumStore {
  constructor() {
    this.storageKeyPrefix = DB_PREFIX;
    this._purgeLegacySeedData();
  }

  _purgeLegacySeedData() {
    try {
      // Clear any legacy demo data from previous test sessions
      const legacyKeys = [
        'dg_album_events',
        'dg_album_guests',
        'dg_album_photos',
        'dg_album_matches',
        'dg_album_clean_events',
        'dg_album_clean_guests',
        'dg_album_clean_photos',
        'dg_album_clean_matches',
        'dg_album_clean_v3_events',
        'dg_album_clean_v3_guests',
        'dg_album_clean_v3_photos',
        'dg_album_clean_v3_matches',
      ];
      legacyKeys.forEach(k => localStorage.removeItem(k));
    } catch {
      // Ignore if localStorage unavailable
    }
  }

  _getStorage(key, defaultVal = []) {
    try {
      const val = localStorage.getItem(this.storageKeyPrefix + key);
      return val ? JSON.parse(val) : defaultVal;
    } catch {
      return defaultVal;
    }
  }

  _setStorage(key, val) {
    try {
      localStorage.setItem(this.storageKeyPrefix + key, JSON.stringify(val));
    } catch (e) {
      console.warn('LocalStorage error:', e);
    }
  }

  getEvents() {
    return this._getStorage('events', []);
  }

  saveEvent(event) {
    const events = this.getEvents();
    const updated = [event, ...events.filter(e => e.id !== event.id)];
    this._setStorage('events', updated);
    return updated;
  }

  deleteEvent(eventId) {
    const events = this.getEvents().filter(e => e.id !== eventId);
    this._setStorage('events', events);
    // Also remove photos and guests for this event
    const photos = this.getPhotos().filter(p => p.eventId !== eventId);
    this._setStorage('photos', photos);
    const guests = this.getGuests().filter(g => g.eventId !== eventId);
    this._setStorage('guests', guests);
    const matches = this.getMatches().filter(m => m.eventId !== eventId);
    this._setStorage('matches', matches);
    return events;
  }

  getGuests(eventId = null, eventCode = null) {
    const all = this._getStorage('guests', []);
    if (!eventId && !eventCode) return all;
    return all.filter(g => {
      if (eventId && (String(g.eventId) === String(eventId) || String(g.event_id) === String(eventId))) {
        return true;
      }
      if (eventCode && g.eventCode && String(g.eventCode).toUpperCase() === String(eventCode).toUpperCase()) {
        return true;
      }
      return false;
    });
  }

  saveGuest(guest) {
    const guests = this.getGuests();
    const updated = [guest, ...guests.filter(g => String(g.id) !== String(guest.id))];
    this._setStorage('guests', updated);
    return updated;
  }

  getPhotos(eventId = null) {
    const all = this._getStorage('photos', []);
    return eventId ? all.filter(p => String(p.eventId) === String(eventId) || String(p.event_id) === String(eventId)) : all;
  }

  addPhotos(newPhotos) {
    const existing = this.getPhotos();
    const updated = [...newPhotos, ...existing];
    this._setStorage('photos', updated);
    return updated;
  }

  getMatches(eventId = null) {
    const all = this._getStorage('matches', []);
    return eventId ? all.filter(m => String(m.eventId) === String(eventId) || String(m.event_id) === String(eventId)) : all;
  }

  getReviewCandidates(eventId = null) {
    const matches = this.getMatches(eventId);
    return matches.filter(m => m.status === 'pending_review');
  }

  approveMatch(matchId) {
    const all = this.getMatches();
    let approvedMatch = null;
    const updated = all.map(m => {
      if (m.matchId === matchId) {
        approvedMatch = { ...m, status: 'confirmed' };
        return approvedMatch;
      }
      return m;
    });
    this._setStorage('matches', updated);

    if (approvedMatch) {
      const guests = this.getGuests();
      const guestMatches = updated.filter(m => m.guestId === approvedMatch.guestId);
      const pendingCount = guestMatches.filter(m => m.status === 'pending_review').length;
      const confirmedCount = guestMatches.filter(m => m.status === 'confirmed').length;

      const updatedGuests = guests.map(g => {
        if (g.id === approvedMatch.guestId) {
          return {
            ...g,
            photosCount: confirmedCount,
            status: pendingCount > 0 ? 'Needs review' : 'Matched',
          };
        }
        return g;
      });
      this._setStorage('guests', updatedGuests);
    }

    return updated;
  }

  rejectMatch(matchId) {
    const all = this.getMatches();
    let rejectedMatch = null;
    const updated = all.map(m => {
      if (m.matchId === matchId) {
        rejectedMatch = { ...m, status: 'rejected' };
        return rejectedMatch;
      }
      return m;
    });
    this._setStorage('matches', updated);

    if (rejectedMatch) {
      const guests = this.getGuests();
      const guestMatches = updated.filter(m => m.guestId === rejectedMatch.guestId);
      const pendingCount = guestMatches.filter(m => m.status === 'pending_review').length;
      const confirmedCount = guestMatches.filter(m => m.status === 'confirmed').length;

      const updatedGuests = guests.map(g => {
        if (g.id === rejectedMatch.guestId) {
          return {
            ...g,
            photosCount: confirmedCount,
            status: pendingCount > 0 ? 'Needs review' : (confirmedCount > 0 ? 'Matched' : 'Processing'),
          };
        }
        return g;
      });
      this._setStorage('guests', updatedGuests);
    }

    return updated;
  }

  /**
   * Genuine AWS Rekognition matches store
   * Updates confirmed matches from the backend API
   */
  setGuestMatches(guestId, matches) {
    const existing = this.getMatches().filter(m => String(m.guestId) !== String(guestId));
    const updated = [...matches, ...existing];
    this._setStorage('matches', updated);
    return updated;
  }

  matchGuestAgainstEventPhotos(guest, eventPhotos) {
    // Face matching is strictly processed in the cloud via AWS Rekognition (backend).
    // Mock string hashing has been completely eliminated to prevent false matches.
    return [];
  }

  getGuestConfirmedPhotos(guestId) {
    const allMatches = this.getMatches();
    const confirmed = allMatches.filter(m => m.guestId === guestId && m.status === 'confirmed');
    return confirmed.map(m => ({
      id: m.photoId,
      url: m.photoUrl,
      category: m.category,
      similarity: m.similarity,
    }));
  }

  clearAllData() {
    this._setStorage('events', []);
    this._setStorage('guests', []);
    this._setStorage('photos', []);
    this._setStorage('matches', []);
  }
}

export const albumStore = new AlbumStore();
export default albumStore;
