import uuid

from models.playlist import Playlist
from models.playlist_song import PlaylistSong


class PlaylistRepository:
    def __init__(self, database_session):
        self.db = database_session

    def create(self, payload: dict):
        playlist = Playlist(id=str(uuid.uuid4()), **payload)
        self.db.add(playlist)
        self.db.commit()
        self.db.refresh(playlist)
        return playlist

    def get_by_user_id(self, user_id: str):
        return self.db.query(Playlist).filter_by(user_id=user_id).order_by(
            Playlist.created_at.desc()
        ).all()

    def get_by_id_and_user_id(self, playlist_id: str, user_id: str):
        return self.db.query(Playlist).filter_by(
            id=playlist_id,
            user_id=user_id,
        ).first()

    def add_song(self, playlist_id: str, song_id: str):
        membership = self.db.query(PlaylistSong).filter_by(
            playlist_id=playlist_id,
            song_id=song_id,
        ).first()
        if membership:
            return False

        self.db.add(PlaylistSong(playlist_id=playlist_id, song_id=song_id))
        self.db.commit()
        return True
