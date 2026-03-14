"""
Blog posts listing and detail endpoints.

GET /api/blogs - List published blog posts with filtering
GET /api/blogs/<slug> - Get blog post details
"""
from flask import request
from sqlalchemy import or_, desc, asc
from tuned.main import main_bp
from tuned.main.schemas import BlogFilterSchema
from tuned.models.blog import BlogPost
from tuned.utils.responses import (
    success_response,
    error_response,
    not_found_response,
    validation_error_response,
    paginated_response
)
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)


@main_bp.route('/api/blogs', methods=['GET'])
def list_blogs():
    """
    List published blog posts with filtering, search, and pagination.
    
    Query parameters:
        - category_id: Filter by category
        - is_published: Filter by published status (default: true)
        - q: Search query (searches title, excerpt, content)
        - sort: Sort field (published_at, created_at, title)
        - order: Sort order (asc, desc)
        - page: Page number
        - per_page: Items per page
    
    Returns:
        JSON response with paginated blog posts
    """
    try:
        # Validate query parameters
        schema = BlogFilterSchema()
        params = schema.load(request.args)
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    
    try:
        # Build query
        query = BlogPost.query
        
        # Filter by published status (default: true for public API)
        is_published = params.get('is_published', True)
        query = query.filter_by(is_published=is_published)
        
        # Filter by category
        if params.get('category_id'):
            query = query.filter_by(category_id=params['category_id'])
        
        # Search by title/excerpt/content
        if params.get('q'):
            search_pattern = f"%{params['q']}%"
            query = query.filter(
                or_(
                    BlogPost.title.ilike(search_pattern),
                    BlogPost.excerpt.ilike(search_pattern),
                    BlogPost.content.ilike(search_pattern)
                )
            )
        
        # Sorting
        sort_field = params.get('sort', 'published_at')
        sort_order = params.get('order', 'desc')
        
        if sort_field == 'published_at':
            query = query.order_by(
                asc(BlogPost.published_at) if sort_order == 'asc' else desc(BlogPost.published_at)
            )
        elif sort_field == 'created_at':
            query = query.order_by(
                asc(BlogPost.created_at) if sort_order == 'asc' else desc(BlogPost.created_at)
            )
        elif sort_field == 'title':
            query = query.order_by(
                asc(BlogPost.title) if sort_order == 'asc' else desc(BlogPost.title)
            )
        
        # Get total count
        total = query.count()
        
        # Paginate
        page = params.get('page', 1)
        per_page = params.get('per_page', 20)
        
        blogs = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialize data
        items = [
            {
                'id': b.id,
                'title': b.title,
                'excerpt': b.excerpt,
                'slug': b.slug,
                'featured_image': b.featured_image,
                'author': b.author,
                'tags': [tag.name for tag in b.tag_list.all()],
                'meta_description': b.meta_description,
                'published_at': b.published_at.isoformat() if b.published_at else None,
                'created_at': b.created_at.isoformat() if b.created_at else None,
                'category': {
                    'id': b.category.id,
                    'name': b.category.name,
                    'slug': b.category.slug,
                    'description': b.category.description
                } if b.category else None
            }
            for b in blogs.items
        ]
        
        logger.info(f'Blogs listed: page {page}, total {total}')
        return paginated_response(
            items=items,
            page=page,
            per_page=per_page,
            total=total
        )
        
    except Exception as e:
        logger.error(f'Error listing blogs: {str(e)}')
        return error_response(
            'Failed to fetch blog posts',
            status=500
        )


@main_bp.route('/api/blogs/<slug>', methods=['GET'])
def get_blog_details(slug):
    """
    Get blog post details by slug.
    
    Only returns published posts for public access.
    Includes full content, category, tags, approved comments, and related posts.
    
    Args:
        slug: Blog post slug
    
    Returns:
        JSON response with blog post details
    """
    try:
        # Query blog post (only published)
        blog = BlogPost.query.filter_by(
            slug=slug,
            is_published=True
        ).first()
        
        if not blog:
            logger.warning(f'Blog post not found or not published: {slug}')
            return not_found_response('Blog post not found')
        
        # Get approved comments count
        approved_comments_count = sum(
            1 for comment in blog.comments if comment.approved
        )
        
        # Get related posts from same category (limit 3, exclude current)
        related_posts = []
        if blog.category:
            related = BlogPost.query.filter(
                BlogPost.category_id == blog.category_id,
                BlogPost.is_published == True,
                BlogPost.id != blog.id
            ).order_by(BlogPost.published_at.desc()).limit(3).all()
            
            related_posts = [
                {
                    'id': p.id,
                    'title': p.title,
                    'excerpt': p.excerpt,
                    'slug': p.slug,
                    'featured_image': p.featured_image,
                    'published_at': p.published_at.isoformat() if p.published_at else None
                }
                for p in related
            ]
        
        # Serialize data
        data = {
            'id': blog.id,
            'title': blog.title,
            'content': blog.content,
            'excerpt': blog.excerpt,
            'slug': blog.slug,
            'featured_image': blog.featured_image,
            'author': blog.author,
            'tags': [tag.name for tag in blog.tag_list.all()],
            'meta_description': blog.meta_description,
            'published_at': blog.published_at.isoformat() if blog.published_at else None,
            'created_at': blog.created_at.isoformat() if blog.created_at else None,
            'category': {
                'id': blog.category.id,
                'name': blog.category.name,
                'slug': blog.category.slug,
                'description': blog.category.description
            } if blog.category else None,
            'comments_count': approved_comments_count,
            'related_posts': related_posts
        }
        
        logger.info(f'Blog post details fetched: {slug}')
        return success_response(data)
        
    except Exception as e:
        logger.error(f'Error fetching blog post details: {str(e)}')
        return error_response(
            'Failed to fetch blog post details',
            status=500
        )
