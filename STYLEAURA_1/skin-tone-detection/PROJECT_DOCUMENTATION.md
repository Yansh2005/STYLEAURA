# Complete Project Documentation: Personalized Outfit Recommendation System

## 1. Project Overview

The **Personalized Outfit Recommendation System** is a computer vision and machine learning-based application designed to analyze a user's image, detect their skin tone and body shape, and provide tailored clothing recommendations based on those features.

The project currently combines multiple AI approaches into a unified pipeline:
1. **Skin Tone Detection:** Uses traditional computer vision and classical machine learning (Logistic Regression) to identify skin pixels and classify the skin tone.
2. **Body Shape Detection:** Utilizes deep learning-based pose landmarks (MediaPipe) to measure anatomical proportions and classify body shapes.
3. **Recommendation Engine:** Employs a rule-based mapping system to match detected features with ideal clothing styles and color palettes.
4. **Backend Service:** Exposes the entire pipeline via a Flask REST API for seamless integration with frontend applications.

---

## 2. System Architecture & Workflow

The system operates through a sequential pipeline when given an input full-body image:

1. **Input:** An image containing a person's full body and face.
2. **Parallel Detection:**
   - **Skin Detector:** Finds the face, isolates skin pixels, and classifies color.
   - **Shape Detector:** Detects full-body landmarks, calculates the shoulder-to-hip ratio, and classifies the shape.
3. **Analysis & Synthesis:** The results are passed to the Recommendation Engine.
4. **Output:** A combined JSON response (or console output) containing the detected skin tone, body shape, confidence metrics, and a list of recommended colors and styles.

---

## 3. Detailed Component Breakdown

### 3.1 Skin Tone Detection (`src/skin_tone_detector.py`)

This component is responsible for isolating skin and determining its natural hue, handling varying lighting conditions through a robust multi-feature approach.

**How it works:**
- **Face Detection (OpenCV Haar Cascade):** The system first converts the image to grayscale and uses OpenCV's `haarcascade_frontalface_default.xml` to locate the largest face in the image, effectively cropping out the background and clothing which might interfere with skin detection.
- **Pixel Classification (Machine Learning):** 
  - The cropped face region is converted from RGB to the HSV (Hue, Saturation, Value) color space.
  - A pre-trained `Logistic Regression` model (`models/skin_classifier.pkl`), trained on the UCI Skin Segmentation Dataset (50,000+ samples), predicts whether each individual pixel is "Skin" or "Non-skin".
- **Skin Tone Classification (Scoring System):**
  - Once skin pixels are isolated, their average HSV values are calculated.
  - The system uses a **Multi-Feature Weighted Scoring** algorithm to classify the tone:
    - **70% Weight on Brightness (V):** Light (>175), Medium (90-190), Dark (<110). Transition zones correctly handle edge cases.
    - **20% Weight on Saturation (S):** Gives a slight boost to the most likely category based on color richness.
    - **10% Weight on Consistency (Std Dev):** Measures how uniform the skin tone is across the face, filtering out shadows and highlights to compute a final Confidence Score.
- **Output:** Classifies tone as **Light**, **Medium**, or **Dark** with a calculated confidence percentage.

### 3.2 Body Shape Detection (`src/body_shape_detector.py`)

This component recently underwent a major refactoring to move away from unreliable silhouette mapping, instead adopting robust skeletal tracking.

**How it works:**
- **Pose Detection (MediaPipe):** The system uses Google's `MediaPipe PoseLandmarker` (`pose_landmarker_full.task`) to detect 33 3D anatomical landmarks on the human body.
- **Measurement Extraction:** 
  - Standard geometric distance (Euclidean) is calculated between the Left and Right Shoulder landmarks (points 11 and 12).
  - Similarly, the distance between the Left and Right Hip landmarks (points 23 and 24) is calculated.
- **Ratio Calculation & Classification:**
  - The shoulder-to-hip width ratio dictates the body shape. Anatomically in MediaPipe, hips are closer together, so a normal ratio is around 1.6 to 1.8.
  - The calculated ratio defines the shape:
    - **Inverted Triangle:** Ratio > 1.85 (Broad shoulders, narrow hips)
    - **Rectangle:** Ratio > 1.8 and <= 1.85 (Relatively straight up and down)
    - **Oval:** Ratio > 1.72 and <= 1.8 (Softer standard proportional balance)
    - **Hourglass:** 1.62 <= Ratio <= 1.72 (Balanced upper and lower body with a defined inward waist, estimated internally)
    - **Triangle:** Ratio < 1.62 (Narrow shoulders, broader hips)
- **Output:** Body shape category and normalized physical measurements.

### 3.3 Outfit Recommendation Engine

Currently housed within `body_shape_detector.py` as `get_outfit_recommendations()`, this is a rule-based engine mapping physical traits to fashion logic.

- **Body Shape to Style Mapping:**
  - *Rectangle:* Belted dresses, peplum tops, A-line skirts.
  - *Triangle:* V-neck tops, structured shoulders, darker colors on bottom.
  - *Inverted Triangle:* Wrap shirts, boyfriend jeans, lighter colors on bottom.
  - *Hourglass:* Wrap dresses, fitted tops, high-waisted pants.
  - *Oval:* Empire waist dresses, monochromatic looks, wide-leg pants.
- **Skin Tone to Color Mapping:**
  - *Light:* Emerald Green, Navy Blue, Jewel Tones.
  - *Medium:* Earth Tones, Olive Green, Warm Beige, Coral.
  - *Dark:* Bright Yellow, Cobalt Blue, Pastels, Vibrant Red.

### 3.4 Backend API Service (`backend/app.py`)

The Flask backend is configured to supply this functionality as a microservice.

- **Architecture:** A lightweight REST API that initializes the heavy ML models globally upon startup to ensure fast response times for subsequent requests.
- **Endpoints:**
  - `GET /api/health`: Health-check endpoint verifying if both detectors loaded successfully.
  - `POST /api/analyze`: Accepts an image file (multipart/form-data), temporarily saves it, runs it through the detection pipeline, and returns a compiled JSON payload with classifications, confidence scores, and recommendations. The temporary file is immediately cleaned up.

---

## 4. Project Structure

```text
skin-tone-detection/
├── backend/
│   └── app.py                     # Flask API backend integrating both detectors
├── dataset/                       # UCI Skin Segmentation Dataset and data files
├── models/
│   └── skin_classifier.pkl        # Pre-trained Logistic Regression skin pixel model
├── notebooks/                     # Jupyter notebooks for data exploration and model training
├── src/
│   ├── body_shape_detector.py     # MediaPipe logic for anatomical measurements
│   ├── skin_tone_detector.py      # OpenCV + ML logic for skin tone extraction
│   ├── test_pipeline.py           # Unified CLI testing script
│   ├── test_multiple_images.py    # Batch testing for skin tone
│   └── train.py                   # Script to train the skin pixel model
├── pose_landmarker_full.task      # MediaPipe pre-trained model mapping body points
├── PROJECT_DOCUMENTATION.md       # This complete architecture and workflow guide
├── requirements.txt               # Dependencies required to run the project
└── test_images/                   # Folder for input images used during local testing
```

---

## 5. Setup & Usage Instructions

### Prerequisites
- Python 3.8+
- Required Libraries: `opencv-python`, `mediapipe`, `scikit-learn`, `numpy`, `pandas`, `Flask`

### Installation
1. Clone the repository and navigate to the project directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Project

**1. Testing via Command Line Interface (CLI):**
To test an image through the entire consolidated pipeline and see recommendations in the terminal:
```bash
python src/test_pipeline.py path/to/your/image.jpg
```

**2. Starting the Backend API Server:**
To launch the Flask REST API locally:
```bash
python backend/app.py
```
*The server will start on `http://0.0.0.0:5000`.*

**3. API Usage Example (cURL):**
```bash
curl -X POST -F "image=@path/to/your/image.jpg" http://localhost:5000/api/analyze
```

---

## 6. Development Milestones Achieved

- Completely replaced former, inaccurate silhouette-based shape detection with modern 3D pose landmark tracking (MediaPipe).
- Evolved skin tone classification from raw brightness thresholds to a sophisticated, multi-feature weighted HSV algorithm achieving significantly higher confidence bounds (up to 100%).
- Successfully integrated separate data science notebooks and detection modules into a unified, modular Python codebase and Flask API.

## 7. Future Next Steps

1. **Frontend Integration:** Build a web or mobile UI consuming the `/api/analyze` endpoint.
2. **Dynamic ML Recommendations:** Transition the recommendation engine from static dictionaries to an intelligent ML-based collaborative filtering or content-based recommendation approach.
3. **Apparel Overlay (Virtual Try-on):** Utilize the detected body landmarks to virtually map recommended clothing items directly onto the user's image.
4. **Lighting Standardization:** Add an image color-correction pipeline before skin-tone detection to neutralize severe artificial lighting impacts (e.g., highly yellow room lights).
