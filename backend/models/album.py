from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from config.database import Base


class Album(Base):
    __tablename__ = "albums"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    artist_id = Column(String, nullable=False)
    release_year = Column(String, nullable=True)
    cover_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
