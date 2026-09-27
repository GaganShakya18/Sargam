class SongRepository:
    def __init__(self, database_session):
        self.db = database_session

    def get_all(self, limit=20, offset=0):
        return []

    def get_by_id(self, song_id: str):
        return {"id": song_id, "title": "Sample Song"}

    def get_trending(self, limit=10):
        return []

    def get_by_genre(self, song_id: str, limit=10):
        return []
