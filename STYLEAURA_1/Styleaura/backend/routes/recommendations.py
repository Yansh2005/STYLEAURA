from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import Recommendation, Analysis
import json

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/create', methods=['POST'])
@jwt_required()
def create_recommendation():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['analysis_id', 'category', 'title', 'description', 'recommendation_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        analysis_id = data['analysis_id']
        
        # Verify analysis belongs to user
        analysis = Analysis.find_by_id(analysis_id)
        if not analysis or analysis.user_id != current_user_id:
            return jsonify({'error': 'Analysis not found or access denied'}), 404
        
        # Create recommendation
        recommendation = Recommendation({
            'user_id': current_user_id,
            'analysis_id': analysis_id,
            'category': data['category'],
            'title': data['title'],
            'description': data['description'],
            'recommendation_type': data['recommendation_type'],
            'tags': data.get('tags', []),
            'priority': data.get('priority', 1),
            'seasonal_relevance': data.get('seasonal_relevance', 'all')
        })
        
        recommendation.save()
        
        return jsonify({
            'message': 'Recommendation created successfully',
            'recommendation': recommendation.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to create recommendation'}), 500

@recommendations_bp.route('/batch', methods=['POST'])
@jwt_required()
def create_recommendations_batch():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('recommendations') or not isinstance(data['recommendations'], list):
            return jsonify({'error': 'Recommendations array is required'}), 400
        
        analysis_id = data.get('analysis_id')
        
        if analysis_id:
            # Verify analysis belongs to user
            analysis = Analysis.find_by_id(analysis_id)
            if not analysis or analysis.user_id != current_user_id:
                return jsonify({'error': 'Analysis not found or access denied'}), 404
        
        created_recommendations = []
        
        for rec_data in data['recommendations']:
            # Validate required fields for each recommendation
            required_fields = ['category', 'title', 'description', 'recommendation_type']
            for field in required_fields:
                if not rec_data.get(field):
                    return jsonify({'error': f'{field} is required for all recommendations'}), 400
            
            recommendation = Recommendation({
                'user_id': current_user_id,
                'analysis_id': analysis_id,
                'category': rec_data['category'],
                'title': rec_data['title'],
                'description': rec_data['description'],
                'recommendation_type': rec_data['recommendation_type'],
                'tags': rec_data.get('tags', []),
                'priority': rec_data.get('priority', 1),
                'seasonal_relevance': rec_data.get('seasonal_relevance', 'all')
            })
            
            recommendation.save()
            created_recommendations.append(recommendation)
        
        return jsonify({
            'message': f'{len(created_recommendations)} recommendations created successfully',
            'recommendations': [rec.to_dict() for rec in created_recommendations]
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to create recommendations'}), 500

@recommendations_bp.route('/<int:recommendation_id>', methods=['GET'])
@jwt_required()
def get_recommendation(recommendation_id):
    try:
        current_user_id = get_jwt_identity()
        
        recommendation = Recommendation.find_by_id(recommendation_id)
        
        if not recommendation or recommendation.user_id != current_user_id:
            return jsonify({'error': 'Recommendation not found'}), 404
        
        return jsonify({
            'recommendation': recommendation.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve recommendation'}), 500

@recommendations_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_recommendations():
    try:
        current_user_id = get_jwt_identity()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        category = request.args.get('category')
        recommendation_type = request.args.get('type')
        analysis_id = request.args.get('analysis_id', type=int)
        
        # Limit per_page to prevent excessive queries
        per_page = min(per_page, 50)
        
        # Build filters
        filters = {}
        if category:
            filters['category'] = category
        if recommendation_type:
            filters['recommendation_type'] = recommendation_type
        if analysis_id:
            filters['analysis_id'] = analysis_id
        
        recommendations = Recommendation.find_by_user(current_user_id, page, per_page, filters)
        total = Recommendation.count_by_user(current_user_id, filters)
        
        total_pages = (total + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        return jsonify({
            'recommendations': [rec.to_dict() for rec in recommendations],
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
        return jsonify({'error': 'Failed to retrieve recommendations'}), 500

@recommendations_bp.route('/analysis/<int:analysis_id>', methods=['GET'])
@jwt_required()
def get_recommendations_by_analysis(analysis_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Verify analysis belongs to user
        analysis = Analysis.find_by_id(analysis_id)
        if not analysis or analysis.user_id != current_user_id:
            return jsonify({'error': 'Analysis not found or access denied'}), 404
        
        recommendations = Recommendation.find_by_analysis(analysis_id)
        
        return jsonify({
            'recommendations': [rec.to_dict() for rec in recommendations]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve recommendations'}), 500

@recommendations_bp.route('/<int:recommendation_id>', methods=['PUT'])
@jwt_required()
def update_recommendation(recommendation_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        recommendation = Recommendation.find_by_id(recommendation_id)
        
        if not recommendation or recommendation.user_id != current_user_id:
            return jsonify({'error': 'Recommendation not found'}), 404
        
        # Update allowed fields
        update_data = {}
        if 'category' in data:
            update_data['category'] = data['category']
        if 'title' in data:
            update_data['title'] = data['title']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'recommendation_type' in data:
            update_data['recommendation_type'] = data['recommendation_type']
        if 'tags' in data:
            update_data['tags'] = data['tags']
        if 'priority' in data:
            update_data['priority'] = data['priority']
        if 'seasonal_relevance' in data:
            update_data['seasonal_relevance'] = data['seasonal_relevance']
        
        if update_data:
            Recommendation.update_by_id(recommendation_id, update_data)
        
        # Get updated recommendation
        updated_recommendation = Recommendation.find_by_id(recommendation_id)
        
        return jsonify({
            'message': 'Recommendation updated successfully',
            'recommendation': updated_recommendation.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update recommendation'}), 500

@recommendations_bp.route('/<int:recommendation_id>', methods=['DELETE'])
@jwt_required()
def delete_recommendation(recommendation_id):
    try:
        current_user_id = get_jwt_identity()
        
        recommendation = Recommendation.find_by_id(recommendation_id)
        
        if not recommendation or recommendation.user_id != current_user_id:
            return jsonify({'error': 'Recommendation not found'}), 404
        
        Recommendation.delete_by_id(recommendation_id)
        
        return jsonify({
            'message': 'Recommendation deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to delete recommendation'}), 500
