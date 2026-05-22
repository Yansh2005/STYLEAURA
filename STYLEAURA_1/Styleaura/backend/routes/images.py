from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from database import UserImage
from utils.validators import validate_image_file
import os
import uuid
from datetime import datetime

images_bp = Blueprint('images', __name__)

@images_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_image():
    try:
        current_user_id = get_jwt_identity()
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        # Validate file
        validation_result = validate_image_file(file)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['message']}), 400
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Create upload directory if it doesn't exist
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # Save file
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Save to database
        user_image = UserImage({
            'user_id': current_user_id,
            'filename': unique_filename,
            'original_filename': secure_filename(file.filename),
            'file_path': file_path,
            'file_size': file_size,
            'mime_type': file.mimetype,
            'uploaded_at': datetime.utcnow()
        })
        
        user_image.save()
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'image': user_image.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to upload image'}), 500

@images_bp.route('/<int:image_id>', methods=['GET'])
@jwt_required()
def get_image(image_id):
    try:
        current_user_id = get_jwt_identity()
        
        image = UserImage.find_by_id(image_id)
        
        if not image or image.user_id != current_user_id:
            return jsonify({'error': 'Image not found'}), 404
        
        return jsonify({
            'image': image.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve image'}), 500

@images_bp.route('/<int:image_id>/file', methods=['GET'])
@jwt_required()
def get_image_file(image_id):
    try:
        current_user_id = get_jwt_identity()
        
        image = UserImage.find_by_id(image_id)
        
        if not image or image.user_id != current_user_id:
            return jsonify({'error': 'Image not found'}), 404
        
        return send_from_directory(
            os.path.dirname(image.file_path),
            os.path.basename(image.file_path),
            mimetype=image.mime_type
        )
        
    except Exception as e:
        return jsonify({'error': 'Failed to serve image file'}), 500

@images_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_images():
    try:
        current_user_id = get_jwt_identity()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Limit per_page to prevent excessive queries
        per_page = min(per_page, 50)
        
        images = UserImage.find_by_user(current_user_id, page, per_page)
        total = UserImage.count_by_user(current_user_id)
        
        total_pages = (total + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        return jsonify({
            'images': [image.to_dict() for image in images],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve images'}), 500

@images_bp.route('/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_image(image_id):
    try:
        current_user_id = get_jwt_identity()
        
        image = UserImage.find_by_id(image_id)
        
        if not image or image.user_id != current_user_id:
            return jsonify({'error': 'Image not found'}), 404
        
        # Delete file from filesystem
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
        
        # Delete from database
        UserImage.delete_by_id(image_id)
        
        return jsonify({
            'message': 'Image deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to delete image'}), 500
