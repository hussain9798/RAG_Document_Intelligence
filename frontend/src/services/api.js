import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (data) => api.post("/api/auth/register", data),
  login: (data) => api.post("/api/auth/login", data),
  me: () => api.get("/api/auth/me"),
};

export const documentsApi = {
  upload: (file, onProgress) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/api/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: onProgress,
    });
  },
  list: () => api.get("/api/documents"),
  get: (id) => api.get(`/api/documents/${id}`),
  remove: (id) => api.delete(`/api/documents/${id}`),
};

export const chatApi = {
  ask: (data) => api.post("/api/chat", data),
  listConversations: () => api.get("/api/conversations"),
  getConversation: (id) => api.get(`/api/conversations/${id}`),
  deleteConversation: (id) => api.delete(`/api/conversations/${id}`),
};

export default api;
