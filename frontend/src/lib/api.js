import axios from 'axios';
import { getGallerySession } from './gallerySession';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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

  searchByFace: (formData, eventId, threshold = 0.6) => {
    // Backend expects event_id and threshold as form data, not query params
    formData.append('event_id', eventId);
    formData.append('threshold', threshold);
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
