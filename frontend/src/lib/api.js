import axios from 'axios';
import { getGallerySession } from './gallerySession';

const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// R2 returns absolute URLs; local photo storage returns paths relative to its
// configured photo directory. Resolve those through the API's protected route.
export function mediaUrl(value) {
  if (!value || /^(https?:|data:|blob:)/i.test(value)) return value;
  const relative = value.replace(/^\/+/, '').replace(/^storage\//, '');
  return `${API_BASE_URL}/storage/${relative}`;
}

function resolveMedia(data) {
  if (!data || typeof data !== 'object') return data;
  if (Array.isArray(data)) return data.map(resolveMedia);
  for (const [key, value] of Object.entries(data)) {
    if ((key === 'file_path' || key === 'cover_photo') && typeof value === 'string') {
      data[key] = mediaUrl(value);
    } else if (value && typeof value === 'object') {
      data[key] = resolveMedia(value);
    }
  }
  return data;
}

api.interceptors.response.use(response => {
  response.data = resolveMedia(response.data);
  return response;
}, error => {
  const requestPath = error.config?.url
    ? new URL(error.config.url, window.location.origin).pathname
    : '';
  const photographerApi = requestPath === '/api/events'
    || requestPath.startsWith('/api/events/')
    || requestPath === '/api/photos/upload'
    || requestPath.startsWith('/api/jobs/');

  // BrowserRouter can navigate to /admin without a full page request. If its
  // first studio API call is rejected, send the photographer to the server-side
  // sign-in page instead of leaving the admin screen in an error state.
  if (error.response?.status === 401 && photographerApi) {
    window.location.assign('/admin/login');
  }
  return Promise.reject(error);
});

function galleryAuthHeader() {
  const session = getGallerySession();
  return session?.token ? { Authorization: `Bearer ${session.token}` } : {};
}

export const eventsAPI = {
  getAll: () => api.get('/api/events'),
  create: (data) => api.post('/api/events', data),
  getById: (id) => api.get(`/api/events/${id}`),
  delete: (id) => api.delete(`/api/events/${id}`),
  processFaces: (id) => api.post(`/api/events/${id}/process-faces`),
};

export const galleryAPI = {
  // Exchange an event code + password for a session token scoped to that event
  access: (accessCode, password) =>
    api.post('/api/gallery/access', { access_code: accessCode, password }),
};

export const photosAPI = {
  // `signal` accepts an AbortController signal so an in-flight upload can be
  // canceled - without it, aborting a bulk upload would still leave every
  // already-dispatched request running to completion.
  upload: (formData, { onProgress, signal } = {}) =>
    api.post('/api/photos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
      signal,
    }),

  getByEvent: (eventId) =>
    api.get(`/api/photos/event/${eventId}`, {
      headers: galleryAuthHeader(),
    }),

  searchByFace: (formData, eventId, threshold = null) => {
    // Backend expects event_id and threshold as form data, not query params.
    // Leave threshold unset by default so the backend's configured default is
    // used consistently across clients.
    formData.append('event_id', eventId);
    if (threshold !== null && threshold !== undefined) {
      formData.append('threshold', threshold);
    }
    return api.post('/api/photos/search', formData, {
      headers: { 'Content-Type': 'multipart/form-data', ...galleryAuthHeader() },
    });
  },
};

export const jobsAPI = {
  getStatus: (jobId) => api.get(`/api/jobs/${jobId}/status`),
  cancel: (jobId) => api.delete(`/api/jobs/${jobId}`),
};

export default api;
