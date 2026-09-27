from typing import Optional

from pydantic import BaseModel


class SongBase(BaseModel):
    title: str
    artist_id: str
    album_id: Optional[str] = None
    duration_seconds: int = 0
    genre: Optional[str] = None
    bpm: Optional[float] = None
    cover_url: Optional[str] = None
    audio_url: Optional[str] = None


class SongCreate(SongBase):
    pass


class SongOut(SongBase):
    id: str

    class Config:
        from_attributes = True
