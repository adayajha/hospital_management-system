const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export async function api(path, options = {}) {
  const token = localStorage.getItem('hsrs_token');
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers }
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'Request failed');
  return data;
}
