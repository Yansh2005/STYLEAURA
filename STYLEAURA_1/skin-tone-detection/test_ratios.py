import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from body_shape_detector import BodyShapeDetector

detector = BodyShapeDetector()
with open('ratios.txt', 'w', encoding='utf-8') as f:
    for i in range(1, 6):
        img = f"test_images/full_body_{i}.png"
        if os.path.exists(img):
            try:
                res = detector.process_image(img)
                m = res['measurements']
                f.write(f"Image {i}: Shoulder: {m['shoulder_width_norm']:.3f}, Hip: {m['hip_width_norm']:.3f}, Ratio: {m['shoulder_hip_ratio']:.3f}, Shape: {res['body_shape']}\n")
            except Exception as e:
                f.write(f"Image {i} Error: {e}\n")
