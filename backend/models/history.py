from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from config.database import Base


class ListeningHistory(Base):
    __tablename__ = "listening_history"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    song_id = Column(String, nullable=False)
    played_at = Column(DateTime(timezone=True), server_default=func.now())
