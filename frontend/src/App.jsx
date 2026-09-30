import React, { useEffect, useRef, useState } from 'react';

import { API_BASE_URL } from './services/apiConfig';
import { fetchSearchHistory, fetchSearchResults, recordSearchQuery } from './services/api';

const initialForm = { email: '', username: '', full_name: '', password: '' };
const defaultPreferences = {
  audio_quality: 'standard',
  streaming_quality: 'standard',
  autoplay: true,
  crossfade: 0,
  explicit_content: true,
  downloads_enabled: false,
  theme: 'midnight-violet',
  dark_mode: true,
};
const defaultPrivacy = {
  listening_history_enabled: true,
  search_history_enabled: true,
  profile_visible: true,
  account_visibility: 'friends',
};

function getStoredAccounts() {
  try {
    const raw = localStorage.getItem('music-account-list');
    return raw ? JSON.parse(raw) : [];
  } catch (error) {
    return [];
  }
}

function getStoredActiveAccount() {
  try {
    const raw = localStorage.getItem('music-active-account');
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
}

function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`;
}

export default function App() {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState(initialForm);
  const [resetForm, setResetForm] = useState({ email: '', new_password: '' });
  const [token, setToken] = useState(localStorage.getItem('music-token') || '');
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [preferences, setPreferences] = useState(defaultPreferences);
  const [privacy, setPrivacy] = useState(defaultPrivacy);
  const [accountList, setAccountList] = useState(getStoredAccounts());
  const [activeAccount, setActiveAccount] = useState(getStoredActiveAccount());
  const [serverHealth, setServerHealth] = useState(false);
  const [message, setMessage] = useState('');
  const [songs, setSongs] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [hasSearched, setHasSearched] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const [songError, setSongError] = useState('');
  const [isLoadingSongs, setIsLoadingSongs] = useState(false);
  const [currentSong, setCurrentSong] = useState(null);
  const [playbackQueue, setPlaybackQueue] = useState([]);
  const [queueIndex, setQueueIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef(null);
  const searchInputRef = useRef(null);
  const endedHandledRef = useRef(false);
  const [isLoading, setIsLoading] = useState(false);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const [selectedSidebar, setSelectedSidebar] = useState(null);
  const [profileForm, setProfileForm] = useState({ username: '', full_name: '', bio: '', profile_image: '' });
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '' });

  const persistAccountList = (nextAccounts) => {
    localStorage.setItem('music-account-list', JSON.stringify(nextAccounts));
    setAccountList(nextAccounts);
  };

  const saveActiveAccount = (nextAccount) => {
    localStorage.setItem('music-active-account', JSON.stringify(nextAccount));
    setActiveAccount(nextAccount);
  };

  const updateAccountList = (account) => {
    const nextAccounts = [
      ...accountList.filter((item) => item.email !== account.email),
      account,
    ];
    persistAccountList(nextAccounts);
    saveActiveAccount(account);
  };

  const fetchProfile = async (currentToken = token) => {
    if (!currentToken) {
      setUser(null);
      setProfile(null);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        headers: {
          Authorization: `Bearer ${currentToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Session expired');
      }

      const data = await response.json();
      setProfile(data);
      setUser(data);
      setProfileForm({
        username: data.username || '',
        full_name: data.full_name || '',
        bio: data.bio || '',
        profile_image: data.profile_image || '',
      });
      setPreferences({
        ...defaultPreferences,
        ...(data.preferences || {}),
      });
      setPrivacy({
        ...defaultPrivacy,
        ...(data.privacy || {}),
      });
    } catch (error) {
      localStorage.removeItem('music-token');
      setToken('');
      setUser(null);
      setProfile(null);
    }
  };

  useEffect(() => {
    if (!token) {
      setUser(null);
      setProfile(null);
      return;
    }

    fetchProfile(token);
  }, [token]);

  useEffect(() => {
    if (!token || !user || !privacy.search_history_enabled) {
      setRecentSearches([]);
      return undefined;
    }

    let active = true;
    fetchSearchHistory(token)
      .then((data) => {
        if (active) setRecentSearches(data.items || []);
      })
      .catch(() => {
        if (active) setRecentSearches([]);
      });

    return () => {
      active = false;
    };
  }, [token, Boolean(user), privacy.search_history_enabled]);

  const performSongSearch = async (query) => {
    const normalizedQuery = query.trim();
    if (!normalizedQuery) {
      setHasSearched(false);
      setSongs([]);
      setSongError('');
      return;
    }

    setSongError('');
    setIsLoadingSongs(true);
    try {
      const data = await fetchSearchResults(normalizedQuery);
      setSongs(data.results || []);
      setHasSearched(true);
      if (privacy.search_history_enabled) {
        try {
          const result = await recordSearchQuery(normalizedQuery, token);
          if (result.saved) {
            setRecentSearches((current) => [
              { query: normalizedQuery },
              ...current.filter((item) => item.query.toLowerCase() !== normalizedQuery.toLowerCase()),
            ].slice(0, 10));
          }
        } catch {
          setSongError('Search completed, but search history could not be saved.');
        }
      }
    } catch (error) {
      setSongError(error.message || 'Music library could not be loaded.');
    } finally {
      setIsLoadingSongs(false);
    }
  };

  const handleSongSearch = (event) => {
    event.preventDefault();
    performSongSearch(searchQuery);
  };

  const playSong = async (song, queue = songs) => {
    const audio = audioRef.current;
    if (!audio) return;

    const nextQueue = queue.length ? queue : [song];
    const nextIndex = nextQueue.findIndex((item) => item.id === song.id);
    audio.pause();
    setPlaybackQueue(nextQueue);
    setQueueIndex(nextIndex);
    setCurrentSong(song);
    setCurrentTime(0);
    setDuration(song.duration_seconds || 0);
    setSongError('');
    audio.src = `${API_BASE_URL}/songs/${encodeURIComponent(song.id)}/stream`;
    audio.load();
    try {
      await audio.play();
      setIsPlaying(true);
    } catch {
      setIsPlaying(false);
      setSongError('Song could not be played.');
    }
  };

  const playNextSong = () => {
    const nextIndex = queueIndex + 1;
    if (nextIndex < 0 || nextIndex >= playbackQueue.length) {
      audioRef.current?.pause();
      setIsPlaying(false);
      return;
    }
    playSong(playbackQueue[nextIndex], playbackQueue);
  };

  const playPreviousSong = () => {
    const audio = audioRef.current;
    if (audio && audio.currentTime > 3) {
      audio.currentTime = 0;
      setCurrentTime(0);
      return;
    }
    const previousIndex = queueIndex - 1;
    if (previousIndex >= 0) playSong(playbackQueue[previousIndex], playbackQueue);
  };

  const handleSongEnded = () => {
    if (endedHandledRef.current) return;
    endedHandledRef.current = true;
    if (preferences.autoplay && queueIndex + 1 < playbackQueue.length) {
      playSong(playbackQueue[queueIndex + 1], playbackQueue);
      return;
    }
    setIsPlaying(false);
  };

  const togglePlayback = async () => {
    const audio = audioRef.current;
    if (!audio || !currentSong) return;
    if (audio.paused) {
      try {
        await audio.play();
        setIsPlaying(true);
      } catch {
        setSongError('Song could not be played.');
      }
    } else {
      audio.pause();
      setIsPlaying(false);
    }
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleResetChange = (event) => {
    const { name, value } = event.target;
    setResetForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');
    setIsLoading(true);

    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/register';
      const payload = mode === 'login'
        ? { email: form.email, password: form.password }
        : {
            email: form.email,
            username: form.username,
            full_name: form.full_name,
            password: form.password,
          };

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(response.status >= 500
          ? 'Music server is unavailable. Please try again.'
          : data.detail || 'Authentication failed');
      }

      if (mode === 'login') {
        localStorage.setItem('music-token', data.access_token);
        setToken(data.access_token);
        updateAccountList({
          id: data.user.id,
          email: data.user.email,
          username: data.user.username,
          full_name: data.user.full_name,
          token: data.access_token,
        });
        setMessage('Login successful');
      } else {
        const loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: form.email,
            password: form.password,
          }),
        });

        const loginData = await loginResponse.json();
        if (!loginResponse.ok) {
          throw new Error(loginResponse.status >= 500
            ? 'Music server is unavailable. Please try again.'
            : loginData.detail || 'Unable to sign in after signup');
        }

        localStorage.setItem('music-token', loginData.access_token);
        setToken(loginData.access_token);
        updateAccountList({
          id: loginData.user.id,
          email: loginData.user.email,
          username: loginData.user.username,
          full_name: loginData.user.full_name,
          token: loginData.access_token,
        });
        setMessage('Account created and signed in successfully');
      }
    } catch (error) {
      const nextMessage = error instanceof TypeError || (error instanceof Error && error.message === 'Failed to fetch')
        ? 'Music server is unavailable. Please try again.'
        : error.message;

      setMessage(nextMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = async (event) => {
    event.preventDefault();
    setMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: resetForm.email,
          new_password: resetForm.new_password,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to reset password');
      }

      setForm((current) => ({ ...current, email: resetForm.email, password: resetForm.new_password }));
      setMessage('Password updated successfully. Please log in with your new password.');
      setShowForgotPassword(false);
      setMode('login');
      setResetForm({ email: '', new_password: '' });
    } catch (error) {
      const nextMessage = error instanceof Error && error.message === 'Failed to fetch'
        ? 'Could not reach the backend server. Start the API and make sure the app is pointing at the correct host.'
        : error.message;

      setMessage(nextMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const saveProfile = async () => {
    if (!token) {
      setMessage('Please log in before updating your profile.');
      return;
    }

    setSettingsLoading(true);
    setMessage('');

    try {
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(profileForm),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to update your profile.');
      }

      setMessage('Profile updated successfully.');
      setUser((current) => ({ ...current, ...data }));
      fetchProfile(token);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to update your profile.');
    } finally {
      setSettingsLoading(false);
    }
  };

  const changePassword = async () => {
    if (!token) {
      setMessage('Please log in before changing your password.');
      return;
    }

    setSettingsLoading(true);
    setMessage('');

    try {
      const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(passwordForm),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to update your password.');
      }

      setMessage('Password updated successfully.');
      setPasswordForm({ current_password: '', new_password: '' });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to update your password.');
    } finally {
      setSettingsLoading(false);
    }
  };

  const updatePreferences = async (key, value) => {
    const nextPreferences = { ...preferences, [key]: value };
    setPreferences(nextPreferences);
    setSettingsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/users/me/preferences`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ [key]: value }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to save preferences.');
      }

      setPreferences(data);
      setMessage('Preferences updated.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to save preferences.');
    } finally {
      setSettingsLoading(false);
    }
  };

  const updatePrivacy = async (key, value) => {
    const nextPrivacy = { ...privacy, [key]: value };
    setPrivacy(nextPrivacy);

    try {
      const response = await fetch(`${API_BASE_URL}/users/me/privacy`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ [key]: value }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to update privacy settings.');
      }

      setPrivacy(data);
      setMessage('Privacy settings updated.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to update privacy settings.');
    }
  };

  const clearHistory = async (type) => {
    const endpoint = type === 'listening' ? '/users/me/listening-history' : '/users/me/search-history';
    setSettingsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to clear history.');
      }

      if (type === 'search') setRecentSearches([]);
      setMessage(type === 'listening' ? 'Listening history cleared.' : 'Search history cleared.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to clear history.');
    } finally {
      setSettingsLoading(false);
    }
  };

  const checkServerStatus = async () => {
    try {
      const response = await fetch(new URL('/health', `${API_BASE_URL}/`).toString());
      setServerHealth(response.ok);
      setMessage(response.ok ? 'Server connection is healthy.' : 'Server unavailable.');
    } catch (error) {
      setServerHealth(false);
      setMessage('Unable to connect to the music server.');
    }
  };

  const retryConnection = () => {
    checkServerStatus();
  };

  const switchAccount = (account) => {
    localStorage.setItem('music-token', account.token);
    setToken(account.token);
    saveActiveAccount(account);
    setMessage(`${account.username || account.full_name} is now active.`);
  };

  const confirmLogout = () => {
    const shouldLogout = window.confirm('Are you sure you want to log out?');
    if (!shouldLogout) {
      return;
    }

    localStorage.removeItem('music-token');
    setToken('');
    setUser(null);
    setProfile(null);
    setMessage('Logged out successfully.');
  };

  const handleLogout = () => {
    confirmLogout();
  };

  if (!token || !user) {
    return (
      <div className="auth-shell">
        <div className="auth-orb orb-one" />
        <div className="auth-orb orb-two" />

        <div className="auth-card">
          <div className="brand-block">
            <div className="brand-mark">S</div>
            <div>
              <p className="eyebrow">Premium listening</p>
              <h1>Sungg</h1>
            </div>
          </div>

          <div className="welcome-copy">
            <h2>Welcome back</h2>
            <p>Your music is waiting for you.</p>
          </div>

          <div className="toggle-row">
            <button
              type="button"
              className={mode === 'login' ? 'tab active' : 'tab'}
              onClick={() => setMode('login')}
            >
              Log in
            </button>
            <button
              type="button"
              className={mode === 'signup' ? 'tab active' : 'tab'}
              onClick={() => setMode('signup')}
            >
              Sign up
            </button>
          </div>

          {showForgotPassword ? (
            <form onSubmit={handleForgotPassword} className="auth-form">
              <label className="input-label">
                <span>Email</span>
                <input
                  className="input-field"
                  name="email"
                  type="email"
                  value={resetForm.email}
                  onChange={handleResetChange}
                  placeholder="you@example.com"
                  required
                />
              </label>

              <label className="input-label">
                <span>New password</span>
                <div className="password-wrap">
                  <input
                    className="input-field"
                    name="new_password"
                    type={showPassword ? 'text' : 'password'}
                    value={resetForm.new_password}
                    onChange={handleResetChange}
                    placeholder="Enter a new password"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword((current) => !current)}
                    aria-label="Toggle password visibility"
                  >
                    {showPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
              </label>

              {message && <p className="status-message">{message}</p>}

              <button type="submit" className="primary-btn auth-submit" disabled={isLoading}>
                {isLoading ? 'Please wait...' : 'Reset password'}
              </button>

              <button
                type="button"
                className="text-btn"
                onClick={() => {
                  setShowForgotPassword(false);
                  setMessage('');
                  setResetForm({ email: '', new_password: '' });
                }}
              >
                Back to login
              </button>
            </form>
          ) : (
            <form onSubmit={handleSubmit} className="auth-form">
              {mode === 'signup' && (
                <>
                  <label className="input-label">
                    <span>Full name</span>
                    <input className="input-field" name="full_name" value={form.full_name} onChange={handleChange} placeholder="Jane Doe" />
                  </label>
                  <label className="input-label">
                    <span>Username</span>
                    <input className="input-field" name="username" value={form.username} onChange={handleChange} placeholder="janedoe" />
                  </label>
                </>
              )}

              <label className="input-label">
                <span>Email</span>
                <input className="input-field" name="email" type="email" value={form.email} onChange={handleChange} placeholder="you@example.com" required />
              </label>

              <label className="input-label">
                <span>Password</span>
                <div className="password-wrap">
                  <input
                    className="input-field"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    value={form.password}
                    onChange={handleChange}
                    placeholder="••••••••"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword((current) => !current)}
                    aria-label="Toggle password visibility"
                  >
                    {showPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
              </label>

              {mode === 'login' && (
                <button
                  type="button"
                  className="text-btn"
                  onClick={() => {
                    setShowForgotPassword(true);
                    setResetForm({ email: form.email, new_password: '' });
                    setMessage('');
                  }}
                >
                  Forgot password?
                </button>
              )}

              {message && <p className="status-message">{message}</p>}
              <button type="submit" className="primary-btn auth-submit" disabled={isLoading}>
                {isLoading ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}
              </button>
            </form>
          )}

          {mode === 'login' && !showForgotPassword && (
            <>
              <div className="divider"><span>or</span></div>
              <button type="button" className="social-btn">
                Continue with Google
              </button>
            </>
          )}

          <p className="auth-footer">
            {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}
            <button
              type="button"
              className="link-inline"
              onClick={() => {
                setMode(mode === 'login' ? 'signup' : 'login');
                setShowForgotPassword(false);
                setMessage('');
              }}
            >
              {mode === 'login' ? 'Sign up' : 'Log in'}
            </button>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <div className="music-app-shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">Good evening</p>
            <h1>{user.username || user.full_name || 'Sungg'}</h1>
          </div>
          <button className="profile-pill" onClick={() => setShowSidebar(true)} aria-label="Open profile and settings">A</button>
        </header>

        <main className="main-content">
          <section className="hero-card">
            <div className="hero-copy">
              <p className="eyebrow muted">Local library</p>
              <h2>Your music</h2>
            </div>
            <button type="button" className="primary-btn compact" onClick={() => songs[0] && playSong(songs[0])} disabled={!songs.length}>Play</button>
          </section>

          {hasSearched && <section className="stats-grid">
            <div className="stat-box"><strong>{hasSearched ? songs.length : recentSearches.length}</strong><span>{hasSearched ? 'Search results' : 'Recent searches'}</span></div>
            <div className="stat-box"><strong>{hasSearched ? new Set(songs.map((song) => song.artist_name).filter(Boolean)).size : ' '}</strong><span>{hasSearched ? 'Artists' : ' '}</span></div>
            <div className="stat-box"><strong>{hasSearched ? new Set(songs.map((song) => song.audio_format).filter(Boolean)).size : ' '}</strong><span>{hasSearched ? 'Formats' : ' '}</span></div>
          </section>}

          <section className="panel">
            <div className="section-head">
              <h3>Music library</h3>
              <span className="catalog-count">{hasSearched ? `${songs.length} results` : ''}</span>
            </div>
            <form className="catalog-search" onSubmit={handleSongSearch}>
              <input
                ref={searchInputRef}
                id="music-search"
                aria-label="Search songs, artists, albums, or genres"
                value={searchQuery}
                onChange={(event) => {
                  const value = event.target.value;
                  setSearchQuery(value);
                  setHasSearched(false);
                  setSongs([]);
                  if (!value.trim()) {
                    setSongError('');
                  }
                }}
                placeholder="Search songs, artists, albums, or genres"
              />
              <button type="submit" className="primary-btn compact" disabled={isLoadingSongs}>{isLoadingSongs ? 'Loading' : 'Search'}</button>
            </form>
            {songError && <p className="catalog-status error-text" role="alert">{songError}</p>}
            {isLoadingSongs && <p className="catalog-status">Loading music library...</p>}
            {!hasSearched && !isLoadingSongs && privacy.search_history_enabled && (
              <div className="recent-searches">
                <h4>Recent searches</h4>
                {recentSearches.length ? recentSearches.map((item) => (
                  <button key={`${item.query}-${item.searched_at || ''}`} type="button" onClick={() => {
                    setSearchQuery(item.query);
                    performSongSearch(item.query);
                  }}>{item.query}</button>
                )) : <p className="catalog-status">Your recent searches will appear here.</p>}
              </div>
            )}
            {!hasSearched && !privacy.search_history_enabled && <p className="catalog-status">Search history is turned off.</p>}
            {hasSearched && !isLoadingSongs && !songs.length && <p className="catalog-status">No songs match that search.</p>}
            {hasSearched && <div className="song-list">
              {songs.map((song) => (
                <article key={song.id} className={currentSong?.id === song.id ? 'library-song active' : 'library-song'}>
                  <div className="song-mark" aria-hidden="true">♫</div>
                  <div className="library-song-info">
                    <strong>{song.title}</strong>
                    <span>{song.artist_name || 'Unknown Artist'}{song.album_title ? ` · ${song.album_title}` : ''}</span>
                  </div>
                  <span className="song-duration">{formatDuration(song.duration_seconds || 0)}</span>
                  <button type="button" className="song-play" onClick={() => playSong(song, songs)} aria-label={`Play ${song.title}`}>▶</button>
                </article>
              ))}
            </div>}
          </section>
        </main>

        {currentSong && (
          <div className="mini-player" aria-label="Mini player">
            <div className="mini-cover small" aria-hidden="true">♫</div>
            <div className="mini-meta">
              <strong>{currentSong.title}</strong>
              <span>{currentSong.artist_name || 'Unknown Artist'}</span>
            </div>
            <button type="button" className="mini-play" onClick={togglePlayback} aria-label={isPlaying ? 'Pause' : 'Play'}>
              {isPlaying ? '❚❚' : '▶'}
            </button>
            <button type="button" className="queue-control" onClick={playPreviousSong} aria-label="Play previous song">|◀</button>
            <button type="button" className="queue-control" onClick={playNextSong} aria-label="Play next song">▶|</button>
            <div className="player-seek">
              <span>{formatDuration(Math.floor(currentTime))}</span>
              <input
                type="range"
                min="0"
                max={duration || currentSong.duration_seconds || 0}
                step="1"
                value={Math.min(currentTime, duration || currentSong.duration_seconds || 0)}
                aria-label="Seek within song"
                disabled={!duration && !currentSong.duration_seconds}
                onChange={(event) => {
                  const nextTime = Number(event.target.value);
                  audioRef.current.currentTime = nextTime;
                  setCurrentTime(nextTime);
                }}
              />
              <span>{formatDuration(duration || currentSong.duration_seconds || 0)}</span>
            </div>
          </div>
        )}
        <audio
          ref={audioRef}
          hidden
          onPlay={() => {
            endedHandledRef.current = false;
            setIsPlaying(true);
          }}
          onLoadedMetadata={(event) => setDuration(Math.floor(event.currentTarget.duration || 0))}
          onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime || 0)}
          onEnded={handleSongEnded}
          onError={() => {
            if (currentSong) {
              setIsPlaying(false);
              setSongError('Song could not be played.');
            }
          }}
        />

        <nav className="bottom-nav" aria-label="Main navigation">
          <button type="button" className="nav-item active">
            <span>Home</span>
          </button>
          <button
            type="button"
            className="nav-item"
            onClick={() => {
              searchInputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
              searchInputRef.current?.focus();
            }}
          >
            <span>Search</span>
          </button>
          <button type="button" className="nav-item">
            <span>Library</span>
          </button>
        </nav>
      </div>

      {showSidebar && (
        <div className="sidebar-overlay" onClick={() => setShowSidebar(false)}>
          <aside className="profile-sidebar" onClick={(event) => event.stopPropagation()}>
            <div className="sidebar-header">
              <button type="button" className="icon-btn" onClick={() => setShowSidebar(false)} aria-label="Close profile sidebar">←</button>
              <h3>Profile</h3>
            </div>

            <div className="sidebar-profile-card">
              <div className="avatar-lg">{(user.username || user.full_name || 'S').slice(0, 1).toUpperCase()}</div>
              <div>
                <strong>{user.username || user.full_name || 'Sungg'}</strong>
                <span>{user.email || 'user@example.com'}</span>
                <small>{user.account_type || 'Free'} account</small>
              </div>
            </div>

            <div className="sidebar-sections">
              <div className="sidebar-section">
                <div className="section-title">Account</div>
                <button type="button" className={selectedSidebar === 'profile' ? 'sidebar-link active' : 'sidebar-link'} onClick={() => setSelectedSidebar('profile')}>View Profile</button>
                <button type="button" className={selectedSidebar === 'edit-profile' ? 'sidebar-link active' : 'sidebar-link'} onClick={() => setSelectedSidebar('edit-profile')}>Edit Profile</button>
                <button type="button" className={selectedSidebar === 'change-password' ? 'sidebar-link active' : 'sidebar-link'} onClick={() => setSelectedSidebar('change-password')}>Change Password</button>
                <button type="button" className={selectedSidebar === 'account-switcher' ? 'sidebar-link active' : 'sidebar-link'} onClick={() => setSelectedSidebar('account-switcher')}>Manage Account</button>
                <button type="button" className={selectedSidebar === 'add-account' ? 'sidebar-link active' : 'sidebar-link'} onClick={() => setSelectedSidebar('add-account')}>Add Account</button>
              </div>

              <div className="sidebar-section">
                <div className="section-title">Music Preferences</div>
                <div className="setting-row">
                  <span>Audio Quality</span>
                  <select value={preferences.audio_quality} onChange={(event) => updatePreferences('audio_quality', event.target.value)}>
                    <option value="standard">Standard</option>
                    <option value="high">High</option>
                    <option value="lossless">Lossless</option>
                  </select>
                </div>
                <div className="setting-row">
                  <span>Streaming Quality</span>
                  <select value={preferences.streaming_quality} onChange={(event) => updatePreferences('streaming_quality', event.target.value)}>
                    <option value="standard">Standard</option>
                    <option value="high">High</option>
                    <option value="hd">HD</option>
                  </select>
                </div>
                <label className="switch-row"><span>Autoplay</span><input type="checkbox" checked={preferences.autoplay} onChange={(event) => updatePreferences('autoplay', event.target.checked)} /></label>
                <div className="setting-row">
                  <span>Crossfade</span>
                  <select value={preferences.crossfade} onChange={(event) => updatePreferences('crossfade', Number(event.target.value))}>
                    <option value={0}>Off</option>
                    <option value={3}>3 sec</option>
                    <option value={6}>6 sec</option>
                    <option value={10}>10 sec</option>
                  </select>
                </div>
                <label className="switch-row"><span>Explicit Content</span><input type="checkbox" checked={preferences.explicit_content} onChange={(event) => updatePreferences('explicit_content', event.target.checked)} /></label>
                <label className="switch-row"><span>Dark Mode</span><input type="checkbox" checked={preferences.dark_mode} onChange={(event) => updatePreferences('dark_mode', event.target.checked)} /></label>
              </div>

              <div className="sidebar-section">
                <div className="section-title">Privacy & Security</div>
                <label className="switch-row"><span>Listening history</span><input type="checkbox" checked={privacy.listening_history_enabled} onChange={(event) => updatePrivacy('listening_history_enabled', event.target.checked)} /></label>
                <label className="switch-row"><span>Search history</span><input type="checkbox" checked={privacy.search_history_enabled} onChange={(event) => updatePrivacy('search_history_enabled', event.target.checked)} /></label>
                <label className="switch-row"><span>Profile visibility</span><input type="checkbox" checked={privacy.profile_visible} onChange={(event) => updatePrivacy('profile_visible', event.target.checked)} /></label>
                <button type="button" className="sidebar-link danger" onClick={() => clearHistory('listening')}>Clear Listening History</button>
                <button type="button" className="sidebar-link danger" onClick={() => clearHistory('search')}>Clear Search History</button>
              </div>

              <div className="sidebar-section">
                <div className="section-title">Notifications</div>
                <label className="switch-row"><span>Push notifications</span><input type="checkbox" defaultChecked /></label>
                <label className="switch-row"><span>New music alerts</span><input type="checkbox" defaultChecked /></label>
                <label className="switch-row"><span>Playlist updates</span><input type="checkbox" defaultChecked /></label>
              </div>

              <div className="sidebar-section">
                <div className="section-title">Storage / Server</div>
                <div className="server-status-row">
                  <span className="status-dot" />
                  <span>{serverHealth ? 'Connected' : 'Offline'}</span>
                </div>
                <div className="setting-row">
                  <span>Server</span>
                  <strong>{API_BASE_URL}</strong>
                </div>
                <button type="button" className="sidebar-link" onClick={checkServerStatus}>Test connection</button>
                <button type="button" className="sidebar-link" onClick={retryConnection}>Retry connection</button>
              </div>

              <div className="sidebar-section">
                <div className="section-title">About</div>
                <button type="button" className="sidebar-link">App version 1.0.0</button>
                <button type="button" className="sidebar-link">About Sungg</button>
                <button type="button" className="sidebar-link">Terms</button>
                <button type="button" className="sidebar-link">Privacy policy</button>
              </div>

              <div className="sidebar-section logout-section">
                <button type="button" className="danger-btn" onClick={confirmLogout}>Logout</button>
              </div>
            </div>
          </aside>
        </div>
      )}

      {selectedSidebar === 'profile' && !showSidebar && (
        <div className="floating-card">
          <h4>Profile details</h4>
          <div className="detail-row"><span>Username</span><strong>{user.username}</strong></div>
          <div className="detail-row"><span>Email</span><strong>{user.email}</strong></div>
          <div className="detail-row"><span>Account</span><strong>{user.account_type || 'Free'}</strong></div>
          <div className="detail-row"><span>Joined</span><strong>{user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Recently'}</strong></div>
        </div>
      )}

      {selectedSidebar === 'edit-profile' && !showSidebar && (
        <div className="floating-card form-card">
          <h4>Edit profile</h4>
          <label className="input-label">
            <span>Username</span>
            <input className="input-field" value={profileForm.username} onChange={(event) => setProfileForm((current) => ({ ...current, username: event.target.value }))} />
          </label>
          <label className="input-label">
            <span>Full name</span>
            <input className="input-field" value={profileForm.full_name} onChange={(event) => setProfileForm((current) => ({ ...current, full_name: event.target.value }))} />
          </label>
          <label className="input-label">
            <span>Bio</span>
            <textarea className="input-field textarea" value={profileForm.bio} onChange={(event) => setProfileForm((current) => ({ ...current, bio: event.target.value }))} />
          </label>
          <label className="input-label">
            <span>Profile image URL</span>
            <input className="input-field" value={profileForm.profile_image} onChange={(event) => setProfileForm((current) => ({ ...current, profile_image: event.target.value }))} />
          </label>
          <button type="button" className="primary-btn auth-submit" onClick={saveProfile} disabled={settingsLoading}>{settingsLoading ? 'Saving...' : 'Save profile'}</button>
        </div>
      )}

      {selectedSidebar === 'change-password' && !showSidebar && (
        <div className="floating-card form-card">
          <h4>Change password</h4>
          <label className="input-label">
            <span>Current password</span>
            <input className="input-field" type={showCurrentPassword ? 'text' : 'password'} value={passwordForm.current_password} onChange={(event) => setPasswordForm((current) => ({ ...current, current_password: event.target.value }))} />
          </label>
          <label className="input-label">
            <span>New password</span>
            <input className="input-field" type={showCurrentPassword ? 'text' : 'password'} value={passwordForm.new_password} onChange={(event) => setPasswordForm((current) => ({ ...current, new_password: event.target.value }))} />
          </label>
          <button type="button" className="text-btn" onClick={() => setShowCurrentPassword((current) => !current)}>{showCurrentPassword ? 'Hide passwords' : 'Show passwords'}</button>
          <button type="button" className="primary-btn auth-submit" onClick={changePassword} disabled={settingsLoading}>{settingsLoading ? 'Updating...' : 'Update password'}</button>
        </div>
      )}

      {selectedSidebar === 'account-switcher' && !showSidebar && (
        <div className="floating-card">
          <h4>Account switcher</h4>
          {accountList.length === 0 ? <p className="muted-copy">No saved accounts.</p> : accountList.map((account) => (
            <button key={account.id || account.email} type="button" className={activeAccount?.email === account.email ? 'account-switch active' : 'account-switch'} onClick={() => switchAccount(account)}>
              <span className="avatar-sm">{(account.username || account.full_name || 'A').slice(0, 1).toUpperCase()}</span>
              <span>
                <strong>{account.username || account.full_name}</strong>
                <small>{account.email}</small>
              </span>
            </button>
          ))}
        </div>
      )}

      {selectedSidebar === 'add-account' && !showSidebar && (
        <div className="floating-card form-card">
          <h4>Add account</h4>
          <p className="muted-copy">Use the sign in form to add another account without removing your current session.</p>
          <button type="button" className="primary-btn auth-submit" onClick={() => setMode('login')}>Open sign in</button>
        </div>
      )}

      {message && <div className="app-banner">{message}</div>}
    </div>
  );
}
