class PlaylistService:
    def __init__(self, repository):
        self.repository = repository

    def create_playlist(self, user_id: str, payload: dict):
        return self.repository.create({"user_id": user_id, **payload})

    def get_user_playlists(self, user_id: str):
        return self.repository.get_by_user_id(user_id)

    def add_song_to_playlist(self, playlist_id: str, song_id: str):
        return self.repository.add_song(playlist_id, song_id)
