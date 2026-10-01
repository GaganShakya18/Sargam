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

export async function fetchSearchSuggestions(query, signal) {
  return getJson(
    `/search/suggestions?q=${encodeURIComponent(query)}`,
    'Search suggestions could not be loaded.',
    { signal },
  );
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

export async function fetchLikedSongs(token) {
  return getJson('/users/me/liked-songs', 'Library could not be loaded.', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function updateSongLike(songId, liked, token) {
  return getJson(
    `/songs/${encodeURIComponent(songId)}/like`,
    "Couldn't update liked songs. Try again.",
    {
      method: liked ? 'POST' : 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    },
  );
}

export async function fetchSongLikeStatus(songId, token) {
  return getJson(`/songs/${encodeURIComponent(songId)}/like-status`, 'Like status could not be loaded.', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function fetchListeningHistory(token) {
  return getJson('/users/me/listening-history?limit=30', 'Listening history could not be loaded.', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function recordListeningHistory(songId, token) {
  return getJson('/users/me/listening-history', 'Listening history could not be saved.', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ song_id: songId }),
  });
}

export async function fetchRecommendations(token) {
  return getJson('/recommendations/?limit=8', 'Recommendations could not be loaded.', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function fetchPlaylists(token) {
  return getJson('/playlists/', 'Playlists could not be loaded.', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function createPlaylist(payload, token) {
  return getJson('/playlists/', "Couldn't create playlist.", {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

export async function addSongToPlaylist(playlistId, songId, token) {
  return getJson(
    `/playlists/${encodeURIComponent(playlistId)}/songs`,
    "Couldn't add song to playlist.",
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ song_id: songId }),
    },
  );
}
