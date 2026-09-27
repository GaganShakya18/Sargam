class RecommendationService:
    def __init__(self, history_repository, song_repository):
        self.history_repository = history_repository
        self.song_repository = song_repository

    def get_recommendations(self, user_id: str, limit: int = 10):
        history = self.history_repository.get_recent_by_user(user_id, limit=limit)
        if not history:
            return self.song_repository.get_trending(limit=limit)
        return self.song_repository.get_by_genre(history[0].song_id, limit=limit)
