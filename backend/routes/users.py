import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.database import get_db
from models.album import Album
from models.artist import Artist
from models.history import ListeningHistory, SearchHistory
from models.song import Song
from repositories.likes_repository import LikesRepository
from repositories.user_repository import UserRepository
from schemas.user_schema import (
    ProfileUpdateRequest,
    SearchHistoryCreate,
    SongHistoryCreate,
    UserPrivacyUpdate,
    UserPreferencesUpdate,
)
from utils.jwt import decode_access_token

router = APIRouter()
security = HTTPBearer()


def _library_song(song, artist_name, album_title):
    return {
        "id": song.id,
        "title": song.title,
        "artist_name": artist_name,
        "album_title": album_title,
        "genre": song.genre,
        "duration_seconds": song.duration_seconds or 0,
        "audio_format": song.audio_format,
        "cover_url": song.cover_url,
    }


def get_authenticated_user(
    db=Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = UserRepository(db).get_by_email(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/me")
def get_current_profile(db=Depends(get_db), current_user=Depends(get_authenticated_user)):
    repo = UserRepository(db)
    preferences = repo.get_preferences(current_user.email)
    privacy = repo.get_privacy(current_user.email)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "bio": current_user.bio,
        "profile_image": current_user.profile_image,
        "account_type": current_user.account_type,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "preferences": {
            "audio_quality": preferences.audio_quality,
            "streaming_quality": preferences.streaming_quality,
            "autoplay": preferences.autoplay,
            "crossfade": preferences.crossfade,
            "explicit_content": preferences.explicit_content,
            "downloads_enabled": preferences.downloads_enabled,
            "theme": preferences.theme,
            "dark_mode": preferences.dark_mode,
        },
        "privacy": {
            "listening_history_enabled": privacy.listening_history_enabled,
            "search_history_enabled": privacy.search_history_enabled,
            "profile_visible": privacy.profile_visible,
            "account_visibility": privacy.account_visibility,
        },
    }


@router.patch("/me")
def update_current_profile(
    payload: ProfileUpdateRequest,
    db=Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    repo = UserRepository(db)
    try:
        user = repo.update_profile(current_user.email, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "bio": user.bio,
        "profile_image": user.profile_image,
        "account_type": user.account_type,
    }


@router.get("/me/preferences")
def get_preferences(db=Depends(get_db), current_user=Depends(get_authenticated_user)):
    repo = UserRepository(db)
    preference = repo.get_preferences(current_user.email)
    return {
        "audio_quality": preference.audio_quality,
        "streaming_quality": preference.streaming_quality,
        "autoplay": preference.autoplay,
        "crossfade": preference.crossfade,
        "explicit_content": preference.explicit_content,
        "downloads_enabled": preference.downloads_enabled,
        "theme": preference.theme,
        "dark_mode": preference.dark_mode,
    }


@router.patch("/me/preferences")
def update_preferences(
    payload: UserPreferencesUpdate,
    db=Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    repo = UserRepository(db)
    try:
        preference = repo.save_preferences(current_user.email, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "audio_quality": preference.audio_quality,
        "streaming_quality": preference.streaming_quality,
        "autoplay": preference.autoplay,
        "crossfade": preference.crossfade,
        "explicit_content": preference.explicit_content,
        "downloads_enabled": preference.downloads_enabled,
        "theme": preference.theme,
        "dark_mode": preference.dark_mode,
    }


@router.get("/me/privacy")
def get_privacy(db=Depends(get_db), current_user=Depends(get_authenticated_user)):
    repo = UserRepository(db)
    privacy = repo.get_privacy(current_user.email)
    return {
        "listening_history_enabled": privacy.listening_history_enabled,
        "search_history_enabled": privacy.search_history_enabled,
        "profile_visible": privacy.profile_visible,
        "account_visibility": privacy.account_visibility,
    }


@router.patch("/me/privacy")
def update_privacy(
    payload: UserPrivacyUpdate,
    db=Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    repo = UserRepository(db)
    privacy = repo.save_privacy(current_user.email, payload.model_dump(exclude_unset=True))
    return {
        "listening_history_enabled": privacy.listening_history_enabled,
        "search_history_enabled": privacy.search_history_enabled,
        "profile_visible": privacy.profile_visible,
        "account_visibility": privacy.account_visibility,
    }


@router.delete("/me/listening-history")
def clear_listening_history(db=Depends(get_db), current_user=Depends(get_authenticated_user)):
    repo = UserRepository(db)
    deleted = repo.delete_listening_history(current_user.email)
    return {"deleted": deleted, "message": "Listening history cleared."}


@router.get("/me/listening-history")
def get_listening_history(
    limit: int = Query(30, ge=1, le=100),
    db=Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    privacy = UserRepository(db).get_privacy(current_user.email)
    if not privacy.listening_history_enabled:
        return {"items": []}
    rows = db.query(ListeningHistory, Song, Artist.name, Album.title).join(
        Song, Song.id == ListeningHistory.song_id
    ).outerjoin(Artist, Artist.id == Song.artist_id).outerjoin(
        Album, Album.id == Song.album_id
    ).filter(
        ListeningHistory.user_id == current_user.id,
        Song.file_path.is_not(None),
    ).order_by(
        ListeningHistory.played_at.desc()
    ).limit(limit).all()
    return {"items": [_library_song(song, artist_name, album_title) for _, song, artist_name, album_title in rows]}


@router.post("/me/listening-history")
def record_listening_history(
    payload: SongHistoryCreate,
    db=Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    song_exists = db.query(Song.id).filter(
        Song.id == payload.song_id,
        Song.file_path.is_not(None),
    ).first()
    if song_exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found.")
    privacy = UserRepository(db).get_privacy(current_user.email)
    if not privacy.listening_history_enabled:
        return {"recorded": False}
    db.add(ListeningHistory(id=str(uuid.uuid4()), user_id=current_user.id, song_id=payload.song_id))
    db.commit()
    return {"recorded": True}


@router.get("/me/liked-songs")
def get_liked_songs(
    limit: int = Query(200, ge=1, le=500),
    db=Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    likes = LikesRepository(db).list_for_user(current_user.id, limit=limit)
    song_ids = [like.song_id for like in likes]
    if not song_ids:
        return {"items": [], "total": 0}
    rows = db.query(Song, Artist.name, Album.title).outerjoin(
        Artist, Artist.id == Song.artist_id
    ).outerjoin(Album, Album.id == Song.album_id).filter(
        Song.id.in_(song_ids), Song.file_path.is_not(None)
    ).all()
    by_id = {song.id: _library_song(song, artist_name, album_title) for song, artist_name, album_title in rows}
    items = [by_id[song_id] for song_id in song_ids if song_id in by_id]
    return {"items": items, "total": len(items)}


@router.delete("/me/search-history")
def clear_search_history(db=Depends(get_db), current_user=Depends(get_authenticated_user)):
    repo = UserRepository(db)
    deleted = repo.delete_search_history(current_user.email)
    return {"deleted": deleted, "message": "Search history cleared."}


@router.get("/me/search-history")
def get_search_history(db=Depends(get_db), current_user=Depends(get_authenticated_user)):
    repo = UserRepository(db)
    privacy = repo.get_privacy(current_user.email)
    searches = repo.get_search_history(current_user.email)
    return {
        "enabled": privacy.search_history_enabled,
        "items": [{"query": item.query, "searched_at": item.searched_at} for item in searches],
    }


@router.post("/me/search-history")
def record_search_history(
    payload: SearchHistoryCreate,
    db=Depends(get_db),
    current_user=Depends(get_authenticated_user),
):
    saved = UserRepository(db).record_search(current_user.email, payload.query)
    return {"saved": saved}


@router.get("/me/sessions")
def list_sessions(db=Depends(get_db), current_user=Depends(get_authenticated_user)):
    repo = UserRepository(db)
    sessions = repo.get_sessions(current_user.email)
    return [{
        "id": item.id,
        "device_name": item.device_name,
        "last_active": item.last_active,
        "created_at": item.created_at,
    } for item in sessions]


@router.delete("/me/sessions/{session_id}")
def delete_session(session_id: str, db=Depends(get_db), current_user=Depends(get_authenticated_user)):
    repo = UserRepository(db)
    try:
        repo.delete_session(current_user.email, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"message": "Session removed."}


@router.get("/")
def list_users():
    return {"items": []}


@router.get("/{user_id}")
def get_user(user_id: str):
    return {"user_id": user_id, "message": "User detail placeholder"}
