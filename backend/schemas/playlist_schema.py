from typing import Optional

from pydantic import BaseModel


class PlaylistBase(BaseModel):
    name: str
    description: Optional[str] = None
    cover_url: Optional[str] = None


class PlaylistCreate(PlaylistBase):
    pass


class PlaylistOut(PlaylistBase):
    id: str
    user_id: str

    class Config:
        from_attributes = True


class PlaylistSongCreate(BaseModel):
    song_id: str
