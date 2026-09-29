import { API_BASE_URL } from './apiConfig';

export async function fetchSongs() {
  const response = await fetch(`${API_BASE_URL}/songs/`);
  return response.json();
}

export async function fetchSearchResults(query) {
  const response = await fetch(`${API_BASE_URL}/search/?q=${encodeURIComponent(query)}`);
  return response.json();
}
