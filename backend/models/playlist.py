from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.sql import func

from config.database import Base


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    cover_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
