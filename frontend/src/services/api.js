import { API_BASE_URL } from './apiConfig';

async function getJson(path, unavailableMessage, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    throw new Error('Music server is unavailable.');
  }

  if (!response.ok) {
    throw new Error(unavailableMessage);
  }
  return response.json();
}

export async function fetchSongs() {
  return getJson('/songs/', 'Music library could not be loaded.');
}

export async function fetchSearchResults(query) {
  return getJson(`/search/?q=${encodeURIComponent(query)}`, 'Music library could not be searched.');
}

export async function fetchSearchHistory(token) {
  return getJson('/users/me/search-history', 'Search history could not be loaded.', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function recordSearchQuery(query, token) {
  return getJson('/users/me/search-history', 'Search history could not be saved.', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });
}
