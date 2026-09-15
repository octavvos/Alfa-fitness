import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
const STORAGE_KEY = "fitness_admin_tokens";

export function getTokens() {
  const raw = localStorage.getItem(STORAGE_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function setTokens(tokens) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
}

export function clearTokens() {
  localStorage.removeItem(STORAGE_KEY);
}

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const tokens = getTokens();
  if (tokens?.access) {
    config.headers.Authorization = `Bearer ${tokens.access}`;
  }
  return config;
});

let refreshPromise = null;

async function refreshAccessToken() {
  const tokens = getTokens();
  if (!tokens?.refresh) throw new Error("No refresh token");
  const { data } = await axios.post(`${BASE_URL}/auth/refresh/`, { refresh: tokens.refresh });
  const updated = { ...tokens, access: data.access };
  setTokens(updated);
  return updated.access;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry && getTokens()?.refresh) {
      original._retry = true;
      try {
        if (!refreshPromise) refreshPromise = refreshAccessToken();
        const access = await refreshPromise;
        refreshPromise = null;
        original.headers.Authorization = `Bearer ${access}`;
        return api(original);
      } catch (refreshError) {
        refreshPromise = null;
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default api;
