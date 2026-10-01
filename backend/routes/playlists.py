from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import get_db
from models.song import Song
from repositories.playlist_repository import PlaylistRepository
from routes.users import get_authenticated_user
from schemas.playlist_schema import PlaylistCreate, PlaylistSongCreate
from services.playlist_service import PlaylistService

router = APIRouter()


@router.get("/")
def list_playlists(
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    playlists = PlaylistService(PlaylistRepository(db)).get_user_playlists(current_user.id)
    return {"items": [{
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "cover_url": playlist.cover_url,
    } for playlist in playlists]}


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_playlist(
    payload: PlaylistCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    playlist = PlaylistService(PlaylistRepository(db)).create_playlist(
        current_user.id,
        payload.model_dump(),
    )
    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "cover_url": playlist.cover_url,
    }


@router.post("/{playlist_id}/songs")
def add_song_to_playlist(
    playlist_id: str,
    payload: PlaylistSongCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    repository = PlaylistRepository(db)
    if repository.get_by_id_and_user_id(playlist_id, current_user.id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found.")
    song_exists = db.query(Song.id).filter(
        Song.id == payload.song_id,
        Song.file_path.is_not(None),
    ).first()
    if song_exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found.")
    added = PlaylistService(repository).add_song_to_playlist(playlist_id, payload.song_id)
    return {"added": added}


@router.get("/{playlist_id}")
def get_playlist(playlist_id: str):
    return {"playlist_id": playlist_id, "message": "Playlist detail placeholder"}
