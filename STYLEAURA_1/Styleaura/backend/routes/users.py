from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import User, UserImage, Analysis, Recommendation

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    try:
        current_user_id = get_jwt_identity()
        
        user = User.find_by_id(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user statistics
        image_count = UserImage.count_by_user(current_user_id)
        analysis_count = Analysis.count_by_user(current_user_id)
        recommendation_count = Recommendation.count_by_user(current_user_id)
        
        profile_data = user.to_dict()
        profile_data.update({
            'statistics': {
                'images_uploaded': image_count,
                'analyses_completed': analysis_count,
                'recommendations_received': recommendation_count
            }
        })
        
        return jsonify({
            'profile': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve user profile'}), 500

@users_bp.route('/history', methods=['GET'])
@jwt_required()
def get_user_history():
    try:
        current_user_id = get_jwt_identity()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        history_type = request.args.get('type', 'all')  # 'all', 'images', 'analyses', 'recommendations'
        
        # Limit per_page to prevent excessive queries
        per_page = min(per_page, 20)
        
        history = []
        
        if history_type in ['all', 'images']:
            images = UserImage.find_by_user(current_user_id, 1, per_page)
            
            for image in images:
                history.append({
                    'type': 'image',
                    'id': image.id,
                    'data': image.to_dict(),
                    'timestamp': image.uploaded_at.isoformat() if image.uploaded_at else None
                })
        
        if history_type in ['all', 'analyses']:
            analyses = Analysis.find_by_user(current_user_id, 1, per_page)
            
            for analysis in analyses:
                history.append({
                    'type': 'analysis',
                    'id': analysis.id,
                    'data': analysis.to_dict(),
                    'timestamp': analysis.created_at.isoformat() if analysis.created_at else None
                })
        
        if history_type in ['all', 'recommendations']:
            recommendations = Recommendation.find_by_user(current_user_id, 1, per_page)
            
            for rec in recommendations:
                history.append({
                    'type': 'recommendation',
                    'id': rec.id,
                    'data': rec.to_dict(),
                    'timestamp': rec.created_at.isoformat() if rec.created_at else None
                })
        
        # Sort by timestamp (most recent first)
        history.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        # Apply pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_history = history[start:end]
        
        return jsonify({
            'history': paginated_history,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(history),
                'has_more': len(history) > end
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve user history'}), 500

@users_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_user_dashboard():
    try:
        current_user_id = get_jwt_identity()
        
        # Get recent activity
        recent_images = UserImage.find_by_user(current_user_id, 1, 5)
        
        recent_analyses = Analysis.find_by_user(current_user_id, 1, 5)
        
        recent_recommendations = Recommendation.find_by_user(current_user_id, 1, 5)
        
        # Get statistics
        total_images = UserImage.count_by_user(current_user_id)
        total_analyses = Analysis.count_by_user(current_user_id)
        total_recommendations = Recommendation.count_by_user(current_user_id)
        
        # Get latest analysis if exists
        latest_analysis_data = Analysis.find_by_user(current_user_id, 1, 1)
        latest_analysis = latest_analysis_data[0] if latest_analysis_data else None
        
        dashboard_data = {
            'statistics': {
                'total_images': total_images,
                'total_analyses': total_analyses,
                'total_recommendations': total_recommendations
            },
            'recent_activity': {
                'images': [img.to_dict() for img in recent_images],
                'analyses': [analysis.to_dict() for analysis in recent_analyses],
                'recommendations': [rec.to_dict() for rec in recent_recommendations]
            },
            'latest_analysis': latest_analysis.to_dict() if latest_analysis else None
        }
        
        return jsonify({
            'dashboard': dashboard_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve user dashboard'}), 500

@users_bp.route('/delete-account', methods=['DELETE'])
@jwt_required()
def delete_user_account():
    try:
        current_user_id = get_jwt_identity()
        
        user = User.find_by_id(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Delete user's data from all collections
        # MongoDB will handle cascade deletion through application logic
        
        # Delete user's images
        images = UserImage.find_by_user(current_user_id, 1, 1000)  # Get all images
        for image in images:
            # Delete file from filesystem
            import os
            if os.path.exists(image.file_path):
                os.remove(image.file_path)
            # Delete from database
            UserImage.delete_by_id(image.id)
        
        # Delete user's analyses (this will also delete related recommendations)
        analyses = Analysis.find_by_user(current_user_id, 1, 1000)
        for analysis in analyses:
            Analysis.delete_by_id(analysis.id)
        
        # Delete any remaining recommendations
        recommendations = Recommendation.find_by_user(current_user_id, 1, 1000)
        for rec in recommendations:
            Recommendation.delete_by_id(rec.id)
        
        # Delete user (this would be handled by MongoDB directly)
        from bson import ObjectId
        from database import users_collection
        users_collection.delete_one({'_id': ObjectId(current_user_id)})
        
        return jsonify({
            'message': 'Account deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to delete account'}), 500
