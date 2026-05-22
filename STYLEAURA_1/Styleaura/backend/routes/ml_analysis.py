import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from database import UserImage, Analysis

# Make sure ml_src is discoverable
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

logger = logging.getLogger(__name__)

ml_analysis_bp = Blueprint('ml_analysis', __name__)

try:
    from ml_src.skin_tone_detector import SkinToneDetector
    from ml_src.body_shape_detector import BodyShapeDetector, get_outfit_recommendations, get_color_palette, get_full_outfit_recommendations
    
    # Initialize Detectors
    model_path = os.path.join(backend_dir, 'ml_models', 'skin_classifier.pkl')
    skin_detector = SkinToneDetector(model_path=model_path)
    shape_detector = BodyShapeDetector()
    detectors_ready = True
except ImportError as e:
    logger.error(f"Error loading ML modules: {e}")
    skin_detector = None
    shape_detector = None
    detectors_ready = False
except Exception as e:
    logger.error(f"Error initializing ML modules: {e}")
    skin_detector = None
    shape_detector = None
    detectors_ready = False

@ml_analysis_bp.route('/analyze/<int:image_id>', methods=['POST'])
@jwt_required()
def analyze_image(image_id):
    if not detectors_ready:
        return jsonify({'error': 'ML Detectors not properly loaded. Check server logs.'}), 500
        
    try:
        current_user_id = get_jwt_identity()
        
        # Verify image belongs to user
        image = UserImage.find_by_id(image_id)
        if not image or str(image.user_id) != str(current_user_id):
            return jsonify({'error': 'Image not found or access denied'}), 404
            
        file_path = image.file_path
        if not os.path.exists(file_path):
            return jsonify({'error': 'Image file missing on server'}), 404
            
        # 1. Detect Skin Tone
        skin_result, _, _ = skin_detector.process_image(file_path)
        skin_tone = skin_result['skin_tone']
        skin_confidence = skin_result['confidence']
        
        # 2. Detect Body Shape + Gender
        shape_result = shape_detector.process_image(file_path)
        body_shape = shape_result['body_shape']
        body_measurements = shape_result['measurements']
        detected_gender = shape_result.get('detected_gender', 'Female')
        gender_confidence = shape_result.get('gender_confidence', 0)
        
        # 3. Full Recommendations (gender-aware outfits, colors, styles)
        full_recs = get_full_outfit_recommendations(skin_tone, body_shape, detected_gender)
        color_palette = get_color_palette(skin_tone)
        
        # 4. Save Analysis to DB
        analysis = Analysis({
            'user_id': current_user_id,
            'image_id': image_id,
            'skin_tone': skin_tone,
            'body_shape': body_shape,
            'confidence_score': skin_confidence,
            'body_measurements': body_measurements,
            'color_palette': color_palette,
            'detected_gender': detected_gender,
            'gender_confidence': float(gender_confidence),
            'style_personality': "Not specified",
            'face_shape': "Not specified",
            'height_estimate': body_measurements.get('height_estimate', "Not specified")
        })
        analysis.save()
        
        return jsonify({
            'message': 'Analysis complete',
            'analysis': analysis.to_dict(),
            'recommendations': full_recs
        }), 200
        
    except Exception as e:
        logger.error(f"Error during ML analysis: {e}")
        return jsonify({'error': str(e)}), 500


@ml_analysis_bp.route('/analyze-direct', methods=['POST'])
def analyze_direct():
    """
    Direct image upload + parallel ML analysis.
    No JWT required — accepts a file upload, runs skin tone and body shape
    detection concurrently, and returns full recommendations.
    """
    if not detectors_ready:
        return jsonify({'error': 'ML models are not loaded. Please check server logs.'}), 500

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided. Use form field name "image".'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    # Save to a temp file
    fd, temp_path = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    try:
        file.save(temp_path)

        # --- Run both detections in PARALLEL ---
        skin_result_holder = {}
        shape_result_holder = {}
        error_holder = {}

        def run_skin_detection():
            try:
                result, _, _ = skin_detector.process_image(temp_path)
                skin_result_holder['data'] = result
            except Exception as e:
                error_holder['skin'] = str(e)

        def run_shape_detection():
            try:
                result = shape_detector.process_image(temp_path)
                shape_result_holder['data'] = result
            except Exception as e:
                error_holder['shape'] = str(e)

        import gc
        gc.collect()
        
        # Run sequentially to save memory and avoid DeepFace OOM on low-RAM systems
        run_skin_detection()
        
        gc.collect() # Free up any intermediate memory before loading DeepFace
        run_shape_detection()

        # --- Validate: ensure at least one human signal was detected ---
        skin_data = skin_result_holder.get('data', {})
        shape_data = shape_result_holder.get('data', {})
        skin_error = error_holder.get('skin')
        shape_error = error_holder.get('shape')

        # If BOTH detectors failed, the image definitely has no human
        if skin_error and shape_error:
            return jsonify({
                'error': 'No human detected in the image.',
                'detail': 'Please upload a clear photo of a real person (full-body or portrait). Screenshots, objects, and non-human images cannot be analyzed.'
            }), 422

        # If the body shape detector failed (non-human image), block regardless of skin
        if shape_error:
            # Check if skin detector also found no real face
            if not skin_data.get('face_detected', True):
                return jsonify({
                    'error': 'No human detected in the image.',
                    'detail': 'Please upload a clear photo of a real person (full-body or portrait). Screenshots, objects, and non-human images cannot be analyzed.'
                }), 422
            # Shape failed but a real face was found — marginal case, allow with warning
            logger.warning(f"Shape detection failed but face was found: {shape_error}")

        # If skin detector failed with insufficient pixels, block
        if skin_error and 'Insufficient skin' in str(skin_error):
            return jsonify({
                'error': 'No human detected in the image.',
                'detail': 'Please upload a clear photo of a real person (full-body or portrait). Screenshots, objects, and non-human images cannot be analyzed.'
            }), 422

        # --- Process results (safe to proceed) ---
        skin_tone = skin_data.get('skin_tone', 'Medium')
        skin_confidence = skin_data.get('confidence', 0)

        body_shape = shape_data.get('body_shape', 'Rectangle')
        body_measurements = shape_data.get('measurements', {})
        detected_gender = shape_data.get('detected_gender', 'Female')
        gender_confidence = shape_data.get('gender_confidence', 0)
        pose_detected = shape_data.get('pose_detected', False)

        # Get full recommendations (gender-aware)
        full_recs = get_full_outfit_recommendations(skin_tone, body_shape, detected_gender)
        color_palette = get_color_palette(skin_tone)

        response = {
            'detected_features': {
                'skin_tone': skin_tone,
                'skin_tone_confidence': float(round(skin_confidence * 100, 1)),
                'body_shape': body_shape,
                'detected_gender': detected_gender,
                'gender_confidence': float(gender_confidence),
                'pose_detected': pose_detected,
                'measurements': body_measurements,
                'skin_error': skin_error,
                'shape_error': shape_error
            },
            'color_palette': color_palette,
            'recommendations': full_recs
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error during direct ML analysis: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

