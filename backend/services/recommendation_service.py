from sqlalchemy import case

from models.album import Album
from models.artist import Artist
from models.history import LikedSong, ListeningHistory
from models.song import Song


class RecommendationService:
    def __init__(self, database_session):
        self.db = database_session

    def get_recommendations(self, user_id: str, limit: int = 10, include_history: bool = True):
        liked_rows = self.db.query(Song).join(
            LikedSong, LikedSong.song_id == Song.id
        ).filter(LikedSong.user_id == user_id).limit(50).all()
        history_rows = []
        if include_history:
            history_rows = self.db.query(Song).join(
                ListeningHistory, ListeningHistory.song_id == Song.id
            ).filter(ListeningHistory.user_id == user_id).order_by(
                ListeningHistory.played_at.desc()
            ).limit(30).all()

        seed_songs = {song.id: song for song in [*liked_rows, *history_rows]}
        if not seed_songs:
            return []

        liked_ids = {song.id for song in liked_rows}
        artist_ids = {song.artist_id for song in seed_songs.values()}
        album_ids = {song.album_id for song in seed_songs.values() if song.album_id}
        genres = {song.genre for song in seed_songs.values() if song.genre}
        score = (
            case((Song.artist_id.in_(artist_ids), 3), else_=0)
            + case((Song.album_id.in_(album_ids), 2), else_=0)
            + case((Song.genre.in_(genres), 1), else_=0)
        )

        query = self.db.query(Song, Artist.name, Album.title, score.label("score")).outerjoin(
            Artist, Artist.id == Song.artist_id
        ).outerjoin(Album, Album.id == Song.album_id).filter(
            Song.file_path.is_not(None),
            ~Song.id.in_(set(seed_songs) | liked_ids),
            (Song.artist_id.in_(artist_ids)
             | Song.album_id.in_(album_ids)
             | Song.genre.in_(genres)),
        ).order_by(score.desc(), Song.title).limit(limit)

        return [
            {
                "id": song.id,
                "title": song.title,
                "artist_name": artist_name,
                "album_title": album_title,
                "genre": song.genre,
                "duration_seconds": song.duration_seconds or 0,
                "cover_url": song.cover_url,
            }
            for song, artist_name, album_title, _ in query.all()
        ]
