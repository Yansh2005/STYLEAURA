import argparse
import sys
import os
import cv2

# Add project root to sys.path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.skin_tone_detector import SkinToneDetector
from src.body_shape_detector import BodyShapeDetector, get_outfit_recommendations

def test_pipeline(image_path):
    print(f"Testing pipeline with image: {image_path}")
    
    # 1. Initialize Detectors
    print("\n[1] Initializing Detectors...")
    skin_detector = SkinToneDetector(model_path=os.path.join(os.path.dirname(__file__), '..', 'models', 'skin_classifier.pkl'))
    shape_detector = BodyShapeDetector()
    
    # 2. Process Image
    print("\n[2] Processing Image...")
    # Skin Tone
    try:
        skin_result, _, _ = skin_detector.process_image(image_path)
        skin_tone = skin_result['skin_tone']
        print(f"Detected Skin Tone: {skin_tone} (Confidence: {skin_result['confidence']:.2f})")
    except Exception as e:
        print(f"Error extracting skin tone: {e}")
        return

    # Body Shape
    try:
        shape_result = shape_detector.process_image(image_path)
        body_shape = shape_result['body_shape']
        measurements = shape_result['measurements']
        print(f"Detected Body Shape: {body_shape}")
        print(f"Measurements: {measurements}")
    except Exception as e:
        print(f"Error extracting body shape: {e}")
        return

    # 3. Recommendations
    print("\n[3] Generating Recommendations...")
    recs = get_outfit_recommendations(skin_tone, body_shape)
    
    print("\n=== FINAL RECOMMENDATION ===")
    print(recs['summary'])
    print("\nSuggested Styles:")
    for style in recs['styles']:
        print(f" - {style}")
    print("\nSuggested Colors:")
    for color in recs['colors']:
        print(f" - {color}")
    print("============================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", help="Path to full body image")
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Image not found at {args.image_path}")
        sys.exit(1)
        
    test_pipeline(args.image_path)
