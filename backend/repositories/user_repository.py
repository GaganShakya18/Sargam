class UserRepository:
    def __init__(self, database_session):
        self.db = database_session

    def get_by_email(self, email: str):
        return None

    def create(self, payload: dict):
        return payload
