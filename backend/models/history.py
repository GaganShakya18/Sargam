from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from config.database import Base


class ListeningHistory(Base):
    __tablename__ = "listening_history"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    song_id = Column(String, nullable=False)
    played_at = Column(DateTime(timezone=True), server_default=func.now())


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    query = Column(String, nullable=False)
    searched_at = Column(DateTime(timezone=True), server_default=func.now())


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, unique=True)
    audio_quality = Column(String, default="standard")
    streaming_quality = Column(String, default="standard")
    autoplay = Column(Boolean, default=True)
    crossfade = Column(Integer, default=0)
    explicit_content = Column(Boolean, default=True)
    downloads_enabled = Column(Boolean, default=False)
    theme = Column(String, default="midnight-violet")
    dark_mode = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserPrivacy(Base):
    __tablename__ = "user_privacy"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, unique=True)
    listening_history_enabled = Column(Boolean, default=True)
    search_history_enabled = Column(Boolean, default=True)
    profile_visible = Column(Boolean, default=True)
    account_visibility = Column(String, default="friends")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    device_name = Column(String, nullable=True)
    session_token = Column(String, nullable=True)
    last_active = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
