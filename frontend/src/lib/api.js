import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const eventsAPI = {
  getAll: () => api.get('/api/events'),
  create: (data) => api.post('/api/events', data),
  getById: (id) => api.get(`/api/events/${id}`),
  delete: (id) => api.delete(`/api/events/${id}`),
  processFaces: (id) => api.post(`/api/events/${id}/process-faces`),
};

export const photosAPI = {
  upload: (formData, onProgress) => 
    api.post('/api/photos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    }),
  
  getByEvent: (eventId) => api.get(`/api/photos/event/${eventId}`),
  
  searchByFace: (formData, eventId, threshold = 0.6) => {
    // Backend expects event_id and threshold as form data, not query params
    formData.append('event_id', eventId);
    formData.append('threshold', threshold);
    return api.post('/api/photos/search', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const jobsAPI = {
  getStatus: (jobId) => api.get(`/api/jobs/${jobId}/status`),
  cancel: (jobId) => api.delete(`/api/jobs/${jobId}`),
};

export default api;
