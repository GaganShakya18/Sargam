class MusicService:
    def __init__(self, repository):
        self.repository = repository

    def get_all_songs(self, limit=20, offset=0):
        return self.repository.get_all(limit=limit, offset=offset)

    def get_song_by_id(self, song_id: str):
        return self.repository.get_by_id(song_id)
