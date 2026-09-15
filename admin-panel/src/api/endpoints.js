import api, { clearTokens, setTokens } from "./client";

export async function login(username, password) {
  const { data } = await api.post("/auth/login/", { username, password });
  setTokens({ access: data.access, refresh: data.refresh });
  return data;
}

export function logout() {
  clearTokens();
}

export const getMe = () => api.get("/auth/me/").then((r) => r.data);

export const getPlans = (params) => api.get("/plans/", { params }).then((r) => r.data);
export const createPlan = (data) => api.post("/plans/", data).then((r) => r.data);
export const updatePlan = (id, data) => api.patch(`/plans/${id}/`, data).then((r) => r.data);

export const getClients = (params) => api.get("/clients/", { params }).then((r) => r.data);
export const createClient = (data) => api.post("/clients/", data).then((r) => r.data);

export const getMemberships = (params) => api.get("/memberships/", { params }).then((r) => r.data);
export const createMembership = (data) => api.post("/memberships/", data).then((r) => r.data);
export const freezeMembership = (id, data) =>
  api.post(`/memberships/${id}/freeze/`, data).then((r) => r.data);
export const cancelMembership = (id) => api.post(`/memberships/${id}/cancel/`).then((r) => r.data);

export const checkAccess = (qr_token) => api.post("/access/check/", { qr_token }).then((r) => r.data);

export const getVisits = (params) => api.get("/visits/", { params }).then((r) => r.data);
export const getAccessLogs = (params) => api.get("/access-logs/", { params }).then((r) => r.data);

export const getExpiringReport = (days) =>
  api.get("/reports/expiring/", { params: { days } }).then((r) => r.data);
export const getDailyReport = (date) =>
  api.get("/reports/daily/", { params: date ? { date } : {} }).then((r) => r.data);
export const getAttendanceReport = () => api.get("/reports/attendance/").then((r) => r.data);
