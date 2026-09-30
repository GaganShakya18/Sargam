from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from models.playlist import Playlist
from routes.users import get_authenticated_user

router = APIRouter()


@router.get("/")
def list_playlists(
    db: Session = Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    playlists = db.query(Playlist).filter_by(user_id=current_user.id).order_by(Playlist.created_at.desc()).all()
    return {"items": [{
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "cover_url": playlist.cover_url,
    } for playlist in playlists]}


@router.post("/")
def create_playlist():
    return {"message": "Create playlist placeholder"}


@router.get("/{playlist_id}")
def get_playlist(playlist_id: str):
    return {"playlist_id": playlist_id, "message": "Playlist detail placeholder"}
