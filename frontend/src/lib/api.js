import axios from 'axios';
import { getGallerySession } from './gallerySession';

const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export function mediaUrl(value) {
  if (!value || /^(https?:|data:|blob:)/i.test(value)) return value;
  const relative = value.replace(/^\/+/, '').replace(/^storage\//, '');
  return `${API_BASE_URL}/storage/${relative}`;
}

function resolveMedia(data) {
  if (!data || typeof data !== 'object') return data;
  if (Array.isArray(data)) return data.map(resolveMedia);
  for (const [key, value] of Object.entries(data)) {
    if ((key === 'file_path' || key === 'cover_photo' || key === 'selfie_path') && typeof value === 'string') {
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
};

export const galleryAPI = {
  access: (accessCode, password) =>
    api.post('/api/gallery/access', { access_code: accessCode, password }),
  getGuestGallery: (guestId) => api.get(`/api/gallery/guest/${guestId}`),
};

export const photosAPI = {
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
};

export const guestsAPI = {
  register: (formData) =>
    api.post('/api/guests/register', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getAll: (filter = null) => {
    const params = typeof filter === 'object' && filter !== null ? filter : (filter ? { event_id: filter } : {});
    return api.get('/api/guests', { params });
  },
  getMatchesForReview: (filter = null) => {
    const params = typeof filter === 'object' && filter !== null ? filter : (filter ? { event_id: filter } : {});
    return api.get('/api/matches/review', { params });
  },
  actionMatch: (matchId, action) =>
    api.post(`/api/matches/${matchId}/action`, { action }),
};

export default api;
