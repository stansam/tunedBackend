"""
Blog comments endpoints.

GET /api/blogs/<slug>/comments - Get approved comments for a blog post
POST /api/blogs/<slug>/comments - Add a comment to a blog post
POST /api/blogs/comments/<id>/react - React to a comment (like/dislike)
"""
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from tuned.main import main_bp
from tuned.main.schemas import BlogCommentSchema, CommentReactionSchema
from tuned.models.blog import BlogPost, BlogComment
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils.responses import (
    success_response,
    error_response,
    not_found_response,
    validation_error_response,
    created_response,
    paginated_response
)
from tuned.utils.decorators import rate_limit
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)


@main_bp.route('/api/blogs/<slug>/comments', methods=['GET'])
def get_blog_comments(slug):
    """
    Get approved comments for a blog post.
    
    Query parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
    
    Returns:
        JSON response with paginated comments
    """
    try:
        # Find blog post
        blog = BlogPost.query.filter_by(slug=slug, is_published=True).first()
        
        if not blog:
            return not_found_response('Blog post not found')
        
        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Query approved comments
        query = BlogComment.query.filter_by(
            post_id=blog.id,
            approved=True
        ).order_by(BlogComment.created_at.asc())
        
        total = query.count()
        
        comments = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialize data
        items = [
            {
                'id': c.id,
                'content': c.content,
                'created_at': c.created_at.isoformat() if c.created_at else None,
                'user': {
                    'id': c.user.id,
                    'name': c.user.get_name(),
                    'profile_pic': c.user.profile_pic
                } if c.user else {
                    'name': c.name,
                    'email': c.email
                }
            }
            for c in comments.items
        ]
        
        logger.info(f'Blog comments fetched for {slug}: page {page}, total {total}')
        return paginated_response(
            items=items,
            page=page,
            per_page=per_page,
            total=total
        )
        
    except Exception as e:
        logger.error(f'Error fetching blog comments: {str(e)}')
        return error_response(
            'Failed to fetch comments',
            status=500
        )


@main_bp.route('/api/blogs/<slug>/comments', methods=['POST'])
@rate_limit(max_requests=5, window=3600)  # 5 comments per hour
def add_blog_comment(slug):
    """
    Add a comment to a blog post.
    
    Can be called by authenticated users (auto-approved) or guests (requires approval).
    Rate limited to 5 comments per hour.
    
    Request body:
        - content: Comment content (required)
        - name: Name (required for guests)
        - email: Email (required for guests)
    
    Returns:
        JSON response with created comment
    """
    try:
        # Validate request data
        schema = BlogCommentSchema()
        data = schema.load(request.get_json() or {})
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    
    try:
        # Find blog post
        blog = BlogPost.query.filter_by(slug=slug, is_published=True).first()
        
        if not blog:
            return not_found_response('Blog post not found')
        
        # Check if user is authenticated (optional JWT)
        user_id = None
        auto_approve = False
        
        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            if identity:
                user_id = identity
                auto_approve = True
        except Exception:
            pass
        
        # For guest comments, require name and email
        if not user_id:
            if not data.get('name') or not data.get('email'):
                return validation_error_response({
                    'name': ['Name is required for guest comments'],
                    'email': ['Email is required for guest comments']
                })
        
        # Create comment
        comment = BlogComment(
            post_id=blog.id,
            content=data['content'],
            user_id=user_id,
            name=data.get('name'),
            email=data.get('email'),
            approved=auto_approve
        )
        
        db.session.add(comment)
        db.session.commit()
        
        logger.info(
            f'New comment on blog {slug}: '
            f'user_id={user_id}, auto_approved={auto_approve}'
        )
        
        # Serialize response
        response_data = {
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at.isoformat() if comment.created_at else None,
            'approved': comment.approved,
            'message': 'Comment added successfully' if auto_approve else 'Comment submitted for approval'
        }
        
        return created_response(
            response_data,
            message='Comment added successfully' if auto_approve else 'Comment submitted for approval'
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error adding blog comment: {str(e)}')
        return error_response(
            'Failed to add comment',
            status=500
        )


@main_bp.route('/api/blogs/comments/<int:comment_id>/react', methods=['POST'])
@jwt_required()
def react_to_comment(comment_id):
    """
    React to a blog comment (like/dislike).
    
    NOTE: This endpoint requires a CommentReaction model to be fully functional.
    For now, it returns a 501 Not Implemented status.
    
    Request body:
        - reaction_type: 'like' or 'dislike'
    
    Returns:
        JSON response
    """
    # TODO: Implement when CommentReaction model is created
    return error_response(
        'Comment reactions are not yet implemented. CommentReaction model needs to be created.',
        status=501
    )
