from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.sql import func

from config.database import Base


class PlaylistSong(Base):
    __tablename__ = "playlist_songs"

    playlist_id = Column(String, ForeignKey("playlists.id", ondelete="CASCADE"), primary_key=True)
    song_id = Column(String, ForeignKey("songs.id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)