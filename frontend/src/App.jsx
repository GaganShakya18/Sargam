import React from 'react';  

const likedSongs = [
  { title: 'Midnight City', artist: 'M83', duration: '3:42', accent: 'linear-gradient(135deg, #ff8a00, #e52e71)' },
  { title: 'Levitating', artist: 'Dua Lipa', duration: '3:23', accent: 'linear-gradient(135deg, #00c6ff, #0072ff)' },
  { title: 'Sunflower', artist: 'Post Malone', duration: '2:38', accent: 'linear-gradient(135deg, #84fab0, #8fd3f4)' },
  { title: 'Heat Waves', artist: 'Glass Animals', duration: '3:58', accent: 'linear-gradient(135deg, #f6d365, #fda085)' },
];

const playlists = [
  { name: 'Chill Vibes', tracks: 24, mood: 'Late night' },
  { name: 'Workout Mix', tracks: 18, mood: 'Energy boost' },
  { name: 'Focus Flow', tracks: 31, mood: 'Deep work' },
  { name: 'Road Trip', tracks: 15, mood: 'Weekend drive' },
];

const recommendations = [
  { title: 'Golden Hour', artist: 'JVKE', reason: 'Because you liked Sunflower', color: '#f7b267' },
  { title: 'Night Changes', artist: 'One Direction', reason: 'Popular with your playlist', color: '#bdb2ff' },
  { title: 'Electric Feel', artist: 'MGMT', reason: 'Trending in Chill Vibes', color: '#90be6d' },
  { title: 'Ocean Eyes', artist: 'Billie Eilish', reason: 'Recommended for your mood', color: '#8ecae6' },
];

const stats = [
  { label: 'Liked songs', value: '248' },
  { label: 'Playlists', value: '12' },
  { label: 'Recommended', value: '36' },
];

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Good evening</p>
          <h1>Sungg</h1>
        </div>
        <button className="profile-pill">A</button>
      </header>

      <section className="hero-card">
        <div>
          <p className="eyebrow muted">Your mix</p>
          <h2>For you</h2>
        </div>
        <button className="primary-btn">Play</button>
      </section>

      <section className="stats-grid">
        {stats.map((stat) => (
          <div key={stat.label} className="stat-box">
            <strong>{stat.value}</strong>
            <span>{stat.label}</span>
          </div>
        ))}
      </section>

      <section className="panel">
        <div className="section-head">
          <h3>Liked songs</h3>
          <a href="#">View all</a>
        </div>

        <div className="song-row">
          {likedSongs.map((song) => (
            <article key={song.title} className="song-card">
              <div className="cover-art" style={{ background: song.accent }}>
                ♫
              </div>
              <h4>{song.title}</h4>
              <p>{song.artist}</p>
              <span>{song.duration}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="section-head">
          <h3>My playlists</h3>
          <a href="#">Create</a>
        </div>

        <div className="playlist-grid">
          {playlists.map((playlist) => (
            <article key={playlist.name} className="playlist-card">
              <div className="playlist-icon">♪</div>
              <div>
                <h4>{playlist.name}</h4>
                <p>{playlist.tracks} tracks</p>
              </div>
              <span>{playlist.mood}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="panel last-panel">
        <div className="section-head">
          <h3>Recommended for you</h3>
          <a href="#">Refresh</a>
        </div>

        <div className="recommendations-list">
          {recommendations.map((item) => (
            <div key={item.title} className="recommendation-item">
              <div className="mini-cover" style={{ background: item.color }}>
                ♫
              </div>
              <div className="recommendation-info">
                <h4>{item.title}</h4>
                <p>{item.artist}</p>
              </div>
              <small>{item.reason}</small>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
