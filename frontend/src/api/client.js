const API_BASE = 'http://127.0.0.1:8000/api/v1';

let accessToken = localStorage.getItem('accessToken') || null;

export function setAccessToken(token) {
  accessToken = token;
  if (token) {
    localStorage.setItem('accessToken', token);
  } else {
    localStorage.removeItem('accessToken');
  }
}

export function getAccessToken() {
  return accessToken || localStorage.getItem('accessToken');
}

export function clearTokens() {
  accessToken = null;
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
}

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refreshToken');
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) {
      clearTokens();
      return false;
    }

    const data = await res.json();
    setAccessToken(data.access_token);
    localStorage.setItem('refreshToken', data.refresh_token);
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

export async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = { ...options.headers };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  let res = await fetch(url, { ...options, headers });

  // If 401 and we have a refresh token, try to refresh
  if (res.status === 401 && localStorage.getItem('refreshToken')) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${accessToken}`;
      res = await fetch(url, { ...options, headers });
    }
  }

  return res;
}

export function getSSEUrl(path, params = {}) {
  const query = new URLSearchParams(params).toString();
  return `${API_BASE}${path}${query ? '?' + query : ''}`;
}

export { API_BASE };
