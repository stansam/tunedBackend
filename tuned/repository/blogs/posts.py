from tuned.models import BlogPost
from tuned.dtos import BlogPostDTO, BlogPostResponseDTO, BlogPostListRequestDTO, BlogPostListResponseDTO
from tuned.repository.exceptions import NotFound, DatabaseError, AlreadyExists
from sqlalchemy.orm import Session, Query
from sqlalchemy import or_, asc, desc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timezone
from tuned.repository.blogs.helper import handle_tags

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

class GetBlogPostByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, id: str) -> BlogPostResponseDTO:
        try:
            post = self.db.query(BlogPost).filter_by(id=id).first()
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

            return [BlogPostResponseDTO.from_model(s) for s in posts]

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching posts: {str(e)}")

class GetPublishedBlogPosts:
    def __init__(self, db: Session, req: BlogPostListRequestDTO) -> None:
        self.db = db
        self.req = req
    
    def execute(self) -> list[BlogPostListResponseDTO]:
        try:
            query = self.db.query(BlogPost).filter_by(is_published=True) #.order_by(BlogPost.published_at.desc()).all()
            post = getBlogPostListResponse(query, self.req)
            if not post:
                post = []
            
            return post

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching posts: {str(e)}")

class UpdateOrDeleteBlogPost:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, id: str, data: BlogPostDTO) -> BlogPostResponseDTO:
        try:
            post = self.db.query(BlogPost).filter_by(id=id).first()
            if not post:
                raise NotFound("post not found")
            
            if data.is_deleted:
                post.is_deleted = data.is_deleted
                post.deleted_at = datetime.now(timezone.utc)
                # TODO: Check on cascading reactions and comments
                post.deleted_by = data.deleted_by
            else:
                if data.title:
                    post.title = data.title
                if data.content:
                    post.content = data.content
                if data.excerpt:
                    post.excerpt = data.excerpt
                if data.featured_image:
                    post.featured_image = data.featured_image
                if data.author:
                    post.author = data.author
                if data.category_id:
                    post.category_id = data.category_id
                if data.meta_description:
                    post.meta_description = data.meta_description
                if data.is_published:
                    post.is_published = data.is_published
                    post.published_at = datetime.now(timezone.utc)
                if data.is_featured:
                    post.is_featured = data.is_featured
                if data.updated_at:
                    post.updated_at = data.updated_at
                if data.updated_by:
                    post.updated_by = data.updated_by
            
            self.db.add(post)
            self.db.flush()
            if data.tags:
                tags_obj = handle_tags(data.tags, self.db)
                post.tags = tags_obj
                
            self.db.commit()
            self.db.refresh(post)

            return BlogPostResponseDTO.from_model(post)

        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while updating post: {str(e)}")   

def getBlogPostListResponse(
    query: Query[BlogPost], req: BlogPostListRequestDTO
) -> list[BlogPostListResponseDTO]:
    if req.category_id:
        query = query.filter_by(category_id=req.category_id)
        
    if req.q:
        search_pattern = f"%{req.q}%"
        query = query.filter(
            or_(
                BlogPost.title.ilike(search_pattern),
                BlogPost.excerpt.ilike(search_pattern),
                BlogPost.content.ilike(search_pattern)
            )
        )

    sort_map = {
        "published_at": BlogPost.published_at,
        "created_at": BlogPost.created_at,
        "title": BlogPost.title,
    }

    sort_field = sort_map.get(req.sort, BlogPost.created_at)
    order_func = asc if req.order == "asc" else desc

    query = query.order_by(order_func(sort_field))

    total = query.order_by(None).count()

    page = max(req.page or 1, 1)
    per_page = min(req.per_page or 10, 100)

    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return BlogPostListResponseDTO(
        blogs=[BlogPostResponseDTO.from_model(s) for s in items],
        total=total,
        page=page,
        per_page=per_page,
        sort=req.sort,
        order=req.order,
    )
        
    
