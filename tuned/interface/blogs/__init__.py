from tuned.repository import Repository

class BlogsService:
    def __init__(self):
        self._repo = Repository.blog
    
    def list_featured_blogs(self):
        return self._repo.get_featured()