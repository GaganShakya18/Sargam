class SearchService:
    def __init__(self, repository):
        self.repository = repository

    def search(self, query: str):
        return self.repository.search(query)
