class HistoryRepository:
    def __init__(self, database_session):
        self.db = database_session

    def get_recent_by_user(self, user_id: str, limit: int = 10):
        return []
