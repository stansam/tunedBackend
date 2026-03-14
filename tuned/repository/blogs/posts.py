from tuned.models import BlogPost
from tuned.dtos import BlogPostDTO, BlogPostResponseDTO
from tuned.repository.exceptions import NotFound, DatabaseError, AlreadyExists
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timezone
from tuned.repository.blogs.helper import handle_tags
from dataclasses import asdict

class CreateBlog:
    def __init__(self, db:Session):
        self.db = db
    def execute(self, data: BlogPostDTO)-> BlogPostResponseDTO:
        try:
            data_dict = data.__dict__.copy()
            tags_list = data_dict.pop("tags", [])
            post = BlogPost(**data_dict)

            self.db.add(post)
            self.db.flush()

            tags_obj = handle_tags(tags_list, self.db)
            post.tags = tags_obj

            self.db.commit()
            self.db.refresh(post)
            return BlogPostResponseDTO.from_model(post)

        except IntegrityError as e:
            self.db.rollback()
            raise AlreadyExists("Post already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while creating post:\n {str(e)}")

class GetBlogPostBySlug:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, slug: str) -> BlogPostResponseDTO:
        try:
            post = self.db.query(BlogPost).filter_by(slug=slug)
            if not post:
                raise NotFound("post not found")

            return BlogPostResponseDTO.from_model(post)

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching post: {str(e)}")
        
class GetFeaturedBlogPosts:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self) -> list[BlogPostResponseDTO]:
        try:
            posts = self.db.query(BlogPost).filter_by(is_featured=True, is_published=True).order_by(BlogPost.published_at.desc()).all()
            if not posts:
                raise NotFound("posts not found")

            return [asdict(BlogPostResponseDTO.from_model(s)) for s in posts]

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching posts: {str(e)}")

class GetPublishedBlogPosts:
    def __init__(self, db: Session) -> None:
        self.db = db
    
    def execute(self) -> list[BlogPostResponseDTO]:
        try:
            posts = self.db.query(BlogPost).filter_by(is_published=True).order_by(BlogPost.published_at.desc()).all()
            if not posts:
                raise NotFound("posts not found")

            return [asdict(BlogPostResponseDTO.from_model(s)) for s in posts]

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching posts: {str(e)}")