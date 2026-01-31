"""
File upload route for client orders.

Handles file uploads for order requirements and additional materials.
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
import os
import logging

from tuned.client import client_bp
from tuned.client.schemas import FileUploadSchema
from tuned.models.order import Order
from tuned.models.user import User
from tuned.extensions import db
from tuned.utils import success_response, error_response, validation_error_response, created_response
from tuned.utils.decorators import rate_limit, log_activity
from tuned.services.notification_service import create_notification
from tuned.models.enums import NotificationType

logger = logging.getLogger(__name__)

# File upload configuration
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'zip', 'rar'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@client_bp.route('/orders/<int:order_id>/files/upload', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=20, window=3600)  # 20 uploads per hour
@log_activity('file_uploaded', 'Order')
def upload_order_file(order_id):
    """
    Upload a file for an order.
    
    Args:
        order_id: ID of the order
        
    Form Data:
        file: File to upload (required)
        description: Description of the file (optional)
        file_category: Category (requirement, reference, sample, other)
    
    Returns:
        201: File uploaded successfully
        404: Order not found
        403: Unauthorized access
        400: Validation error or invalid file
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Verify order exists and user has access
        order = Order.query.filter_by(
            id=order_id,
            client_id=current_user_id,
            is_deleted=False
        ).first()
        
        if not order:
            return error_response('Order not found', status=404)
        
        # Check if file is present
        if 'file' not in request.files:
            return error_response('No file provided', status=400)
        
        file = request.files['file']
        
        if file.filename == '':
            return error_response('No file selected', status=400)
        
        if not allowed_file(file.filename):
            return error_response(
                f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}',
                status=400
            )
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return error_response(
                f'File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024):.0f}MB',
                status=400
            )
        
        # Validate metadata
        schema = FileUploadSchema()
        try:
            metadata = schema.load(request.form.to_dict())
        except ValidationError as e:
            return validation_error_response(e.messages)
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        new_filename = f"{order.order_number}_{timestamp}_{filename}"
        
        # Save file (In production, upload to S3 or similar)
        upload_folder = os.path.join('uploads', 'orders', str(order.id))
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, new_filename)
        file.save(file_path)
        
        logger.info(
            f'File uploaded for order {order_id}: {new_filename} '
            f'({file_size} bytes) by user {current_user_id}'
        )
        
        # In a full implementation, save file metadata to database
        # (Create an OrderFile model)
        
        # Notify admins about file upload
        try:
            admins = User.query.filter_by(is_admin=True, is_active=True).all()
            for admin in admins:
                create_notification(
                    user_id=admin.id,
                    title=f'File Uploaded - {order.order_number}',
                    message=f'{order.client.get_name()} uploaded a file for "{order.title}"',
                    type=NotificationType.INFO,
                    link=f'/admin/orders/{order.id}/files'
                )
        except Exception as e:
            logger.error(f'Notification error for file upload on order {order_id}: {str(e)}')
        
        # Prepare response
        file_data = {
            'order_id': order.id,
            'filename': new_filename,
            'original_filename': filename,
            'size': file_size,
            'description': metadata.get('description'),
            'category': metadata.get('file_category', 'other'),
            'uploaded_at': datetime.now(timezone.utc).isoformat()
        }
        
        return created_response(
            data={'file': file_data},
            message='File uploaded successfully'
        )
        
    except Exception as e:
        logger.error(f'Error uploading file for order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while uploading the file', status=500)


@client_bp.route('/orders/<int:order_id>/files', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=100, window=60)
def get_order_files(order_id):
    """
    Get list of files uploaded for an order.
    
    Args:
        order_id: ID of the order
    
    Returns:
        200: List of files
        404: Order not found
        403: Unauthorized access
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Verify order exists and user has access
        order = Order.query.filter_by(
            id=order_id,
            client_id=current_user_id,
            is_deleted=False
        ).first()
        
        if not order:
            return error_response('Order not found', status=404)
        
        # In a full implementation, fetch files from OrderFile model
        # For now, scan the upload directory
        upload_folder = os.path.join('uploads', 'orders', str(order.id))
        
        files_data = []
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                file_path = os.path.join(upload_folder, filename)
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    files_data.append({
                        'filename': filename,
                        'size': file_stat.st_size,
                        'uploaded_at': datetime.fromtimestamp(file_stat.st_ctime, tz=timezone.utc).isoformat()
                    })
        
        logger.info(f'Retrieved {len(files_data)} files for order {order_id}')
        
        return success_response(
            data={'files': files_data},
            message=f'Retrieved {len(files_data)} files'
        )
        
    except Exception as e:
        logger.error(f'Error retrieving files for order {order_id}: {str(e)}', exc_info=True)
        return error_response('An error occurred while retrieving files', status=500)
