from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from config.database import Base


class Song(Base):
    __tablename__ = "songs"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    artist_id = Column(String, nullable=False)
    album_id = Column(String, nullable=True)
    duration_seconds = Column(Integer, default=0)
    genre = Column(String, nullable=True)
    file_path = Column(Text, nullable=True)
    audio_format = Column(String(16), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    bpm = Column(Float, nullable=True)
    cover_url = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    lyrics = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
