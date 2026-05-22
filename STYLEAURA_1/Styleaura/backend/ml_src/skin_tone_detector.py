"""
Skin Tone Detection Pipeline
============================
This script:
1. Loads a face image
2. Detects the face region using OpenCV Haar Cascade
3. Extracts skin pixels using the trained ML model
4. Classifies skin tone as Light/Medium/Dark
5. Displays the result
"""

import cv2
import numpy as np
import pickle
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')  # Suppress sklearn warnings for cleaner output


class SkinToneDetector:
    """
    A class to detect skin tone from face images.
    """
    
    def __init__(self, model_path="models/skin_classifier.pkl"):
        """
        Initialize the detector by loading the trained model.
        
        Args:
            model_path: Path to the trained skin classifier model
        """
        # Load the trained model
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)
        
        # Initialize OpenCV Haar Cascade face detection
        # This is built-in with OpenCV, no extra dependencies needed
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            raise RuntimeError("Could not load Haar Cascade classifier. OpenCV installation may be incomplete.")
        
        print("[OK] Skin Tone Detector initialized successfully!")
    
    def detect_face(self, image):
        """
        Detect face region in the image using OpenCV Haar Cascade.
        Falls back to a skin-region crop from the upper body if no face is found
        (handles full-body photos where the face is small or off-angle).
        
        Args:
            image: Input image (BGR format from OpenCV)
            
        Returns:
            face_region: Cropped face/skin region (BGR format)
            face_bbox: Bounding box coordinates (x, y, width, height)
        """
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Try with relaxed parameters first for full-body photos
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(20, 20)
        )
        
        if len(faces) == 0:
            # Fallback: try even more permissive detection
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=1,
                minSize=(15, 15)
            )
        
        if len(faces) > 0:
            # Use the largest detected face
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            x, y, width, height = faces[0]
            x = max(0, x)
            y = max(0, y)
            width = min(width, w - x)
            height = min(height, h - y)
            face_region = image[y:y+height, x:x+width]
            print(f"[OK] Face detected at: x={x}, y={y}, width={width}, height={height}")
            return face_region, (x, y, width, height), True  # True = real face found
        
        # No face found — use upper-center crop as skin tone sample
        # (covers face/neck area in most portrait or full-body poses)
        print("[WARN] No face detected — using upper-center crop as skin tone fallback.")
        crop_top = 0
        crop_bottom = max(1, int(h * 0.45))   # Top 45% of image
        crop_left = max(0, int(w * 0.20))     # Middle 60% horizontally
        crop_right = min(w, int(w * 0.80))
        fallback_region = image[crop_top:crop_bottom, crop_left:crop_right]
        fallback_bbox = (crop_left, crop_top, crop_right - crop_left, crop_bottom - crop_top)
        return fallback_region, fallback_bbox, False  # False = no real face, using fallback crop
    
    def extract_skin_pixels(self, face_image):
        """
        Extract skin pixels from face region using the trained ML model.
        
        Args:
            face_image: Face region image (BGR format)
            
        Returns:
            skin_pixels: Array of skin pixel RGB values
        """
        # Convert BGR to RGB (OpenCV uses BGR, but our model was trained on RGB)
        rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        
        # Reshape image to list of pixels
        pixels = rgb_image.reshape(-1, 3)
        
        # Convert entire RGB image to HSV at once (much faster than pixel-by-pixel)
        # Reshape back to image shape for cv2.cvtColor, then reshape again
        hsv_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)
        hsv_pixels = hsv_image.reshape(-1, 3)
        
        # Convert to DataFrame to match training format (prevents sklearn warnings)
        hsv_df = pd.DataFrame(hsv_pixels, columns=['H', 'S', 'V'])
        
        # Predict which pixels are skin (label 1 = skin, 2 = non-skin)
        predictions = self.model.predict(hsv_df)
        
        # Extract only skin pixels (where prediction == 1)
        skin_mask = predictions == 1
        skin_pixels = pixels[skin_mask]
        
        print(f"[OK] Extracted {len(skin_pixels)} skin pixels from {len(pixels)} total pixels")
        
        return skin_pixels
    
    def classify_skin_tone(self, skin_pixels):
        """
        Classify skin tone as Light, Medium, or Dark using improved multi-feature approach.
        
        IMPROVEMENTS:
        1. Uses all HSV features (H, S, V) instead of just brightness
        2. Weighted scoring system for better accuracy
        3. Improved confidence calculation based on feature consistency
        
        Args:
            skin_pixels: Array of skin pixel RGB values
            
        Returns:
            tone: String classification ("Light", "Medium", or "Dark")
            confidence: Confidence score (0-1)
            avg_v: Average brightness value for reference
        """
        if len(skin_pixels) == 0:
            raise ValueError("No skin pixels found in the image. Please upload a photo of a person.")
        
        # VALIDATION GATE: If the skin pixel count is critically low, the image likely
        # doesn't contain a person (e.g. it's a screenshot, landscape, or object photo).
        MIN_SKIN_PIXELS = 50
        if len(skin_pixels) < MIN_SKIN_PIXELS:
            raise ValueError(
                f"Insufficient skin detected ({len(skin_pixels)} pixels). "
                "Please upload a clear photo of a person with visible skin."
            )
        
        # Convert skin pixels to HSV efficiently
        num_pixels = len(skin_pixels)
        rgb_reshaped = skin_pixels.reshape(1, num_pixels, 3).astype(np.uint8)
        hsv_reshaped = cv2.cvtColor(rgb_reshaped, cv2.COLOR_RGB2HSV)
        hsv_values = hsv_reshaped.reshape(num_pixels, 3)
        
        # Extract all HSV features
        h_values = hsv_values[:, 0]  # Hue (0-179)
        s_values = hsv_values[:, 1]  # Saturation (0-255)
        v_values = hsv_values[:, 2]  # Value/Brightness (0-255)
        
        # Calculate statistics
        avg_h = np.mean(h_values)
        avg_s = np.mean(s_values)
        avg_v = np.mean(v_values)
        std_v = np.std(v_values)  # Standard deviation for consistency check
        
        # IMPROVED CLASSIFICATION: Multi-feature weighted scoring
        
        # Score for each category (higher = more likely)
        light_score = 0
        medium_score = 0
        dark_score = 0
        
        # 1. PRIMARY FEATURE: Brightness (V) - 70% weight
        # Use overlapping ranges for better boundary handling
        # Light: V > 175 (with transition zone 175-190)
        # Medium: 90 <= V <= 190 (wider range with transitions)
        # Dark: V < 110 (with transition zone 90-110)
        
        # Light scoring (V > 175, peak at V > 190)
        if avg_v > 175:
            if avg_v > 190:
                light_score += 0.7 * 1.0  # Clearly light
            else:
                # Transition zone 175-190: decreasing light score
                light_score += 0.7 * ((avg_v - 175) / 15)
                # Also give some medium score in transition
                medium_score += 0.7 * ((190 - avg_v) / 15) * 0.6
        
        # Medium scoring (90 <= V <= 190, peak at V = 145)
        if 90 <= avg_v <= 190:
            if 120 <= avg_v <= 170:
                # Core medium range (peak at 145)
                medium_score += 0.7 * (1.0 - abs(avg_v - 145) / 50)
            elif avg_v < 120:
                # Lower transition (90-120)
                medium_score += 0.7 * ((avg_v - 90) / 30)
            elif 170 < avg_v <= 190:
                # Upper transition (170-190) - also give medium score
                medium_score += 0.7 * ((190 - avg_v) / 20) * 0.8
        
        # Dark scoring (V < 110, peak at V < 90)
        if avg_v < 110:
            if avg_v < 90:
                dark_score += 0.7 * 1.0  # Clearly dark
            else:
                # Transition zone 90-110: decreasing dark score
                dark_score += 0.7 * ((110 - avg_v) / 20)
                # Also give some medium score in transition
                medium_score += 0.7 * ((avg_v - 90) / 20) * 0.5
        
        # 2. SECONDARY FEATURE: Saturation (S) - 20% weight
        # Higher saturation often indicates more defined skin tone
        saturation_factor = avg_s / 255.0
        
        # Add saturation boost to the category with highest brightness score
        if light_score >= medium_score and light_score >= dark_score:
            light_score += 0.2 * saturation_factor
        elif medium_score >= light_score and medium_score >= dark_score:
            medium_score += 0.2 * saturation_factor
        else:
            dark_score += 0.2 * saturation_factor
        
        # 3. CONSISTENCY CHECK: Standard deviation - 10% weight
        # Lower std = more consistent skin tone = higher confidence
        consistency = 1.0 - min(1.0, std_v / 50.0)  # Normalize std (typical range 0-50)
        if light_score > medium_score and light_score > dark_score:
            light_score += 0.1 * consistency
        elif medium_score > light_score and medium_score > dark_score:
            medium_score += 0.1 * consistency
        else:
            dark_score += 0.1 * consistency
        
        # Determine classification
        scores = {
            'Light': light_score,
            'Medium': medium_score,
            'Dark': dark_score
        }
        
        tone = max(scores, key=scores.get)
        max_score = scores[tone]
        
        # Calculate confidence based on:
        # 1. How much the winning score exceeds others
        # 2. Consistency of brightness (lower std = higher confidence)
        second_best = sorted(scores.values(), reverse=True)[1]
        score_margin = max_score - second_best
        
        # Confidence combines score margin and consistency
        confidence = min(1.0, (max_score * 0.7 + score_margin * 2.0 * 0.3))
        
        # Boost confidence if brightness is very consistent
        if std_v < 15:  # Very consistent skin tone
            confidence = min(1.0, confidence * 1.2)
        
        print(f"[OK] Average HSV: H={avg_h:.1f}, S={avg_s:.1f}, V={avg_v:.2f}")
        print(f"[OK] Scores - Light: {light_score:.3f}, Medium: {medium_score:.3f}, Dark: {dark_score:.3f}")
        
        return tone, float(confidence), float(avg_v)
    
    def process_image(self, image_path):
        """
        Complete pipeline: Load image, detect face, extract skin, classify tone.
        
        Args:
            image_path: Path to the input image
            
        Returns:
            result: Dictionary with classification results
        """
        print(f"\n{'='*50}")
        print(f"Processing: {image_path}")
        print(f"{'='*50}\n")
        
        # Step 1: Load image
        print("Step 1: Loading image...")
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")
        print("[OK] Image loaded successfully")
        
        # Step 2: Detect face
        print("\nStep 2: Detecting face...")
        face_region, face_bbox, face_detected = self.detect_face(image)
        
        # Step 3: Extract skin pixels
        print("\nStep 3: Extracting skin pixels using ML model...")
        skin_pixels = self.extract_skin_pixels(face_region)
        
        # Step 4: Classify skin tone
        print("\nStep 4: Classifying skin tone...")
        tone, confidence, avg_v = self.classify_skin_tone(skin_pixels)
        
        # Prepare result
        result = {
            "skin_tone": tone,
            "confidence": confidence,
            "avg_v": avg_v,  # Average brightness value for analysis
            "face_bbox": face_bbox,
            "face_detected": face_detected,   # True = real face, False = fallback crop
            "num_skin_pixels": len(skin_pixels)
        }
        
        return result, image, face_region


def main():
    """
    Main function to run the skin tone detection pipeline.
    """
    # Initialize detector
    detector = SkinToneDetector(model_path="models/skin_classifier.pkl")
    
    # Check if test_images directory has any images
    test_dir = Path("test_images")
    if not test_dir.exists():
        print("ERROR: test_images/ directory not found!")
        return
    
    # Find image files
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp"]
    image_files = []
    for ext in image_extensions:
        image_files.extend(list(test_dir.glob(f"*{ext}")))
        image_files.extend(list(test_dir.glob(f"*{ext.upper()}")))
    
    if not image_files:
        print("ERROR: No images found in test_images/ directory!")
        print("Please add a face image to test_images/ folder.")
        return
    
    # Process the first image found
    image_path = str(image_files[0])
    
    try:
        # Process image
        result, original_image, face_region = detector.process_image(image_path)
        
        # Display results
        print(f"\n{'='*50}")
        print("FINAL RESULT")
        print(f"{'='*50}")
        print(f"Skin Tone Classification: {result['skin_tone']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Number of skin pixels detected: {result['num_skin_pixels']}")
        print(f"{'='*50}\n")
        
        # Display images
        # Draw bounding box on original image
        x, y, w, h = result['face_bbox']
        annotated_image = original_image.copy()
        cv2.rectangle(annotated_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(annotated_image, f"Skin Tone: {result['skin_tone']}", 
                   (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show images
        cv2.imshow("Original Image with Detection", annotated_image)
        cv2.imshow("Face Region", face_region)
        
        print("Press any key to close the windows...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure the image contains a clear face")
        print("2. Check that the image path is correct")
        print("3. Make sure OpenCV is properly installed: pip install opencv-python")


if __name__ == "__main__":
    main()
