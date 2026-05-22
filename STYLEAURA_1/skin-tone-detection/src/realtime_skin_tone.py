"""
Real-Time Skin Tone Detection
=============================

This script uses your existing `SkinToneDetector` class to:
- Read frames from the webcam
- Detect the face in each frame
- Extract skin pixels and classify skin tone
- Overlay the result (Light / Medium / Dark + confidence) on the video
"""

import cv2
import time
from skin_tone_detector import SkinToneDetector


def run_realtime_skin_tone():
    """
    Run real-time skin tone detection using the webcam.

    Steps:
    1. Open webcam stream
    2. For each frame:
       - Detect face
       - Extract skin pixels
       - Classify skin tone
       - Draw bounding box and label
    3. Press 'q' to quit
    """
    # 1. Initialize detector (loads model + Haar cascade)
    detector = SkinToneDetector(model_path="models/skin_classifier.pkl")

    # 2. Open default webcam (0). Change to 1/2 if multiple cameras.
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open webcam.")
        return

    print("\n[INFO] Real-time skin tone detection started.")
    print("[INFO] Press 'q' in the window to quit.\n")

    # To avoid heavy computation on every frame, we classify every Nth frame
    FRAME_INTERVAL = 10  # classify every 10th frame
    frame_count = 0

    # Last known classification (to keep label stable between detections)
    last_tone = "Unknown"
    last_confidence = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("ERROR: Failed to read frame from webcam.")
                break

            frame_count += 1

            # Make a copy to draw on
            display_frame = frame.copy()

            # Only run full pipeline every FRAME_INTERVAL frames
            if frame_count % FRAME_INTERVAL == 0:
                try:
                    # Use the same pipeline as for images, but directly on the frame
                    # We do NOT resize here to keep coordinates consistent
                    face_region, face_bbox = detector.detect_face(frame)

                    # Extract skin pixels from the detected face
                    skin_pixels = detector.extract_skin_pixels(face_region)

                    # Classify skin tone
                    tone, confidence, avg_v = detector.classify_skin_tone(skin_pixels)

                    last_tone = tone
                    last_confidence = confidence

                    # Draw bounding box on display_frame
                    x, y, w, h = face_bbox
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                except Exception as e:
                    # If detection/classification fails for a frame, keep previous result
                    # but do not crash the loop
                    # Optional: print(e) for debugging
                    pass

            # Always draw the last known result (even on frames where we didn't recompute)
            label = f"Tone: {last_tone} ({last_confidence * 100:.1f}%)"
            cv2.putText(
                display_frame,
                label,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            # Show the frame
            cv2.imshow("Real-Time Skin Tone Detection", display_frame)

            # Exit if user presses 'q'
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        print("\n[INFO] Real-time detection stopped.\n")


if __name__ == "__main__":
    run_realtime_skin_tone()

