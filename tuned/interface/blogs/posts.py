from tuned.repository import Repository

class GetFeaturedBlogPosts:
    def __init__(self):
        self._repo = Repository.blog

    def execute(self):
        return self._repo.get_featured()