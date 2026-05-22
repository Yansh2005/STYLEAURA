from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import Analysis, UserImage
import json

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/create', methods=['POST'])
@jwt_required()
def create_analysis():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('image_id'):
            return jsonify({'error': 'Image ID is required'}), 400
        
        image_id = data['image_id']
        
        # Verify image belongs to user
        image = UserImage.find_by_id(image_id)
        if not image or image.user_id != current_user_id:
            return jsonify({'error': 'Image not found or access denied'}), 404
        
        # Check if analysis already exists for this image
        existing_analysis = Analysis.find_by_image(image_id)
        if existing_analysis:
            return jsonify({'error': 'Analysis already exists for this image'}), 409
        
        # Create analysis with provided data or defaults
        analysis = Analysis({
            'user_id': current_user_id,
            'image_id': image_id,
            'skin_tone': data.get('skin_tone'),
            'body_shape': data.get('body_shape'),
            'style_personality': data.get('style_personality'),
            'confidence_score': data.get('confidence_score'),
            'color_palette': data.get('color_palette', []),
            'face_shape': data.get('face_shape'),
            'height_estimate': data.get('height_estimate'),
            'body_measurements': data.get('body_measurements', {})
        })
        
        analysis.save()
        
        return jsonify({
            'message': 'Analysis created successfully',
            'analysis': analysis.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to create analysis'}), 500

@analysis_bp.route('/<int:analysis_id>', methods=['GET'])
@jwt_required()
def get_analysis(analysis_id):
    try:
        current_user_id = get_jwt_identity()
        
        analysis = Analysis.find_by_id(analysis_id)
        
        if not analysis or analysis.user_id != current_user_id:
            return jsonify({'error': 'Analysis not found'}), 404
        
        return jsonify({
            'analysis': analysis.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve analysis'}), 500

@analysis_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_analyses():
    try:
        current_user_id = get_jwt_identity()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Limit per_page to prevent excessive queries
        per_page = min(per_page, 50)
        
        analyses = Analysis.find_by_user(current_user_id, page, per_page)
        total = Analysis.count_by_user(current_user_id)
        
        total_pages = (total + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        return jsonify({
            'analyses': [analysis.to_dict() for analysis in analyses],
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
        return jsonify({'error': 'Failed to retrieve analyses'}), 500

@analysis_bp.route('/<int:analysis_id>', methods=['PUT'])
@jwt_required()
def update_analysis(analysis_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        analysis = Analysis.find_by_id(analysis_id)
        
        if not analysis or analysis.user_id != current_user_id:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Update allowed fields
        update_data = {}
        if 'skin_tone' in data:
            update_data['skin_tone'] = data['skin_tone']
        if 'body_shape' in data:
            update_data['body_shape'] = data['body_shape']
        if 'style_personality' in data:
            update_data['style_personality'] = data['style_personality']
        if 'confidence_score' in data:
            update_data['confidence_score'] = data['confidence_score']
        if 'color_palette' in data:
            update_data['color_palette'] = data['color_palette']
        if 'face_shape' in data:
            update_data['face_shape'] = data['face_shape']
        if 'height_estimate' in data:
            update_data['height_estimate'] = data['height_estimate']
        if 'body_measurements' in data:
            update_data['body_measurements'] = data['body_measurements']
        
        if update_data:
            Analysis.update_by_id(analysis_id, update_data)
        
        # Get updated analysis
        updated_analysis = Analysis.find_by_id(analysis_id)
        
        return jsonify({
            'message': 'Analysis updated successfully',
            'analysis': updated_analysis.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update analysis'}), 500

@analysis_bp.route('/<int:analysis_id>', methods=['DELETE'])
@jwt_required()
def delete_analysis(analysis_id):
    try:
        current_user_id = get_jwt_identity()
        
        analysis = Analysis.find_by_id(analysis_id)
        
        if not analysis or analysis.user_id != current_user_id:
            return jsonify({'error': 'Analysis not found'}), 404
        
        Analysis.delete_by_id(analysis_id)
        
        return jsonify({
            'message': 'Analysis deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to delete analysis'}), 500

@analysis_bp.route('/image/<int:image_id>', methods=['GET'])
@jwt_required()
def get_analysis_by_image(image_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Verify image belongs to user
        image = UserImage.find_by_id(image_id)
        if not image or image.user_id != current_user_id:
            return jsonify({'error': 'Image not found or access denied'}), 404
        
        analysis = Analysis.find_by_image(image_id)
        
        if not analysis:
            return jsonify({'error': 'Analysis not found for this image'}), 404
        
        return jsonify({
            'analysis': analysis.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve analysis'}), 500
