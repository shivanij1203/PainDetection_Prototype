import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const videoService = {
  getAll: () => api.get('/videos/'),
  getOne: (id) => api.get(`/videos/${id}/`),
  getFrames: (id, page = 1, perPage = 20) =>
    api.get(`/videos/${id}/frames/?page=${page}&per_page=${perPage}`),
  exportAnnotations: (id, format = 'csv') =>
    api.get(`/videos/${id}/export/?format=${format}`, { responseType: 'blob' }),
};

export const frameService = {
  getOne: (id) => api.get(`/frames/${id}/`),
};

export const annotationService = {
  create: (data) => api.post('/annotations/', data),
  update: (id, data) => api.put(`/annotations/${id}/`, data),
  delete: (id) => api.delete(`/annotations/${id}/delete/`),
};

export const statisticsService = {
  get: () => api.get('/statistics/'),
};

export const nipsService = {
  getScale: () => api.get('/nips-scale/'),
};

export default api;
