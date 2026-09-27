from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_playlists():
    return {"items": []}


@router.post("/")
def create_playlist():
    return {"message": "Create playlist placeholder"}


@router.get("/{playlist_id}")
def get_playlist(playlist_id: str):
    return {"playlist_id": playlist_id, "message": "Playlist detail placeholder"}
