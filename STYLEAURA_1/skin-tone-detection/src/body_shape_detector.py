import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os

class BodyShapeDetector:
    def __init__(self, model_asset_path=None):
        if model_asset_path is None:
            # Default to the one in the project root
            model_asset_path = os.path.join(os.path.dirname(__file__), '..', 'pose_landmarker_full.task')
        
        if not os.path.exists(model_asset_path):
            raise FileNotFoundError(f"Pose landmarker model not found at {model_asset_path}")

        base_options = python.BaseOptions(model_asset_path=model_asset_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def process_image(self, image_path_or_array):
        if isinstance(image_path_or_array, str):
            mp_image = mp.Image.create_from_file(image_path_or_array)
        else:
            image_rgb = cv2.cvtColor(image_path_or_array, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

        results = self.detector.detect(mp_image)
        
        if not results.pose_landmarks or len(results.pose_landmarks) == 0:
            raise ValueError("No pose landmarks detected. Please ensure full body is visible.")
            
        landmarks = results.pose_landmarks[0]
        
        def dist(lm1, lm2):
            return np.sqrt((lm1.x - lm2.x)**2 + (lm1.y - lm2.y)**2 + (lm1.z - lm2.z)**2)
            
        shoulder_width = dist(landmarks[11], landmarks[12])
        hip_width = dist(landmarks[23], landmarks[24])
        
        # Calculate ratio
        # MediaPipe hip landmarks are anatomically closer together than shoulder landmarks
        # The typical human shoulder-to-MediaPipe-hip ratio is around 1.6 to 1.8.
        ratio = shoulder_width / hip_width
        
        shape = "Rectangle"
        if ratio > 1.85:
            shape = "Inverted Triangle"
        elif ratio < 1.62:
            shape = "Triangle"
        elif 1.62 <= ratio <= 1.72:
            shape = "Hourglass"
        elif 1.72 < ratio <= 1.85:
            # We classify slightly broader standard shapes as rectangles/ovals
            shape = "Oval" if ratio > 1.8 else "Rectangle"

        waist_width_est = hip_width * 0.75 if shape == "Hourglass" else hip_width * 0.9
        
        return {
            "body_shape": shape,
            "measurements": {
                "shoulder_width_norm": float(shoulder_width),
                "hip_width_norm": float(hip_width),
                "waist_width_est": float(waist_width_est),
                "shoulder_hip_ratio": float(ratio)
            }
        }

def get_outfit_recommendations(skin_tone, body_shape):
    """
    Given a skin tone and body shape, return suitable clothing styles and colors.
    """
    recommendation = {
        "styles": [],
        "colors": [],
        "summary": ""
    }
    
    # Body Shape Mapping
    shape_styles = {
        "Rectangle": ["Belted dresses", "Peplum tops", "A-line skirts", "High-waisted trousers"],
        "Triangle": ["V-neck tops", "Structured shoulders", "Darker colors on bottom", "A-line dresses"],
        "Inverted Triangle": ["V-neck lines", "Wrap shirts", "A-line skirts", "Boyfriend jeans", "Lighter colors on bottom"],
        "Hourglass": ["Wrap dresses", "Fitted tops", "High-waisted pants", "V-necks"],
        "Oval": ["Empire waist dresses", "Monochromatic looks", "V-neck tops", "Wide-leg pants"]
    }
    recommendation["styles"] = shape_styles.get(body_shape, ["Comfortable fits", "Tailored basics"])
    
    # Skin Tone Mapping
    tone_colors = {
        "Light": ["Emerald Green", "Navy Blue", "Jewel Tones", "Ruby Red"],
        "Medium": ["Earth Tones", "Olive Green", "Mustard Yellow", "Warm Beige", "Coral"],
        "Dark": ["Bright Yellow", "Cobalt Blue", "Pastels", "Vibrant Red", "White"]
    }
    recommendation["colors"] = tone_colors.get(skin_tone, ["Neutral colors", "Black and White"])
    
    recommendation["summary"] = f"For your {body_shape} body shape and {skin_tone} skin tone, we recommend {', '.join(recommendation['styles'])} in colors like {', '.join(recommendation['colors'])}."
    
    return recommendation
