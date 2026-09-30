import uuid

from models.history import LikedSong


class LikesRepository:
    def __init__(self, database_session):
        self.db = database_session

    def list_for_user(self, user_id: str, limit: int = 200):
        return (
            self.db.query(LikedSong)
            .filter_by(user_id=user_id)
            .order_by(LikedSong.created_at.desc())
            .limit(limit)
            .all()
        )

    def is_liked(self, user_id: str, song_id: str) -> bool:
        return self.db.query(LikedSong.id).filter_by(user_id=user_id, song_id=song_id).first() is not None

    def add(self, user_id: str, song_id: str) -> bool:
        if self.is_liked(user_id, song_id):
            return False
        self.db.add(LikedSong(id=str(uuid.uuid4()), user_id=user_id, song_id=song_id))
        self.db.commit()
        return True

    def remove(self, user_id: str, song_id: str) -> bool:
        deleted = self.db.query(LikedSong).filter_by(user_id=user_id, song_id=song_id).delete()
        self.db.commit()
        return deleted > 0