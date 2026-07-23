const STORAGE_KEY = 'gallery_session';

/**
 * Persists the unlocked gallery session (token + event summary) so a
 * returning guest doesn't have to re-enter the event code/password every
 * visit. The token itself carries its own expiry (checked server-side) -
 * this is just local caching of "what the guest last unlocked."
 */
export function saveGallerySession(session) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function getGallerySession() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function clearGallerySession() {
  localStorage.removeItem(STORAGE_KEY);
}
