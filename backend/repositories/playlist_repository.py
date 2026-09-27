class PlaylistRepository:
    def __init__(self, database_session):
        self.db = database_session

    def create(self, payload: dict):
        return payload

    def get_by_user_id(self, user_id: str):
        return []
