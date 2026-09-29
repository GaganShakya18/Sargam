import { API_BASE_URL } from './apiConfig';

async function getJson(path, unavailableMessage) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`);
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
