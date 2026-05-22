"""
Flask backend for the clothing recommendation system.
"""

from __future__ import annotations

import logging
import os
import tempfile
from http import HTTPStatus

from flask import Flask, jsonify, request
import cv2

# Add project root to sys.path so we can import from src
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.skin_tone_detector import SkinToneDetector
    from src.body_shape_detector import BodyShapeDetector, get_outfit_recommendations
except ImportError as e:
    logging.warning(f"Could not import detection modules: {e}")
    SkinToneDetector = None
    BodyShapeDetector = None
    get_outfit_recommendations = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize detectors globally so they are only loaded once
skin_detector = SkinToneDetector(model_path=os.path.join(os.path.dirname(__file__), '..', 'models', 'skin_classifier.pkl')) if SkinToneDetector else None
shape_detector = BodyShapeDetector() if BodyShapeDetector else None


@app.route("/api/health", methods=["GET"])
def health_check():
    """Simple health-check endpoint."""
    ready = skin_detector is not None and shape_detector is not None
    return jsonify({"status": "ok", "detectors_ready": ready}), HTTPStatus.OK

@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Analyze an uploaded image for skin tone, body shape, and outfit recommendations."""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), HTTPStatus.BAD_REQUEST
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), HTTPStatus.BAD_REQUEST

    if not skin_detector or not shape_detector:
        return jsonify({"error": "Detectors not loaded"}), HTTPStatus.INTERNAL_SERVER_ERROR

    try:
        # Save uploaded file to temp file
        fd, temp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        file.save(temp_path)
        
        # 1. Detect Skin Tone
        skin_result, _, _ = skin_detector.process_image(temp_path)
        skin_tone = skin_result['skin_tone']
        
        # 2. Detect Body Shape
        shape_result = shape_detector.process_image(temp_path)
        body_shape = shape_result['body_shape']
        
        # 3. Get Recommendations
        recommendations = get_outfit_recommendations(skin_tone, body_shape)
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify({
            "detected_features": {
                "skin_tone": skin_tone,
                "skin_tone_confidence": skin_result['confidence'],
                "body_shape": body_shape,
                "measurements": shape_result['measurements']
            },
            "recommendations": recommendations
        }), HTTPStatus.OK
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

if __name__ == "__main__":
    # For local development only. In production, use a WSGI server (gunicorn, etc.).
    app.run(host="0.0.0.0", port=5000, debug=True)
