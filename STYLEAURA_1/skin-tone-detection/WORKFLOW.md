# Project Workflow - Visual Summary

## Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT: Face Image                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Face Detection                                          │
│  ────────────────────────                                        │
│  • OpenCV Haar Cascade                                            │
│  • Detects face region                                            │
│  • Crops face area                                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Image Preprocessing                                     │
│  ────────────────────────                                        │
│  • Convert BGR → RGB                                             │
│  • Convert RGB → HSV                                              │
│  • Extract all pixels from face region                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Skin Pixel Extraction                                   │
│  ────────────────────────                                        │
│  • Load trained model (skin_classifier.pkl)                      │
│  • Predict skin/non-skin for each pixel                          │
│  • Filter: Keep only skin pixels (label = 1)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Feature Analysis                                        │
│  ────────────────────────                                        │
│  • Calculate average H, S, V values                              │
│  • Calculate standard deviation (consistency)                     │
│  • Extract statistics from skin pixels                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Skin Tone Classification                               │
│  ────────────────────────                                        │
│  Multi-Feature Weighted Scoring:                                 │
│  • Brightness (V): 70% weight                                    │
│  • Saturation (S): 20% weight                                    │
│  • Consistency: 10% weight                                       │
│                                                                   │
│  Categories:                                                     │
│  • Light: V > 175                                                 │
│  • Medium: 90 ≤ V ≤ 190                                          │
│  • Dark: V < 110                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  OUTPUT: Classification Result                                   │
│  ────────────────────────                                        │
│  • Skin Tone: Light / Medium / Dark                              │
│  • Confidence: 0-100%                                            │
│  • Statistics: H, S, V values                                    │
│  • Visualization: Bounding box + face region                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Training Phase (Already Completed)

```
┌─────────────────────────────────────────────────────────────────┐
│  UCI Skin Segmentation Dataset                                  │
│  • Format: RGB + Label (1=Skin, 2=Non-skin)                     │
│  • 50,000+ samples                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Preprocessing                                                  │
│  • Convert RGB → HSV                                             │
│  • Extract features: H, S, V                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Model Training                                                 │
│  • Algorithm: Logistic Regression                                │
│  • Features: H, S, V                                            │
│  • Task: Binary Classification (Skin vs Non-skin)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Save Model                                                     │
│  • File: models/skin_classifier.pkl                              │
│  • Ready for inference                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Classification Logic (Improved Method)

```
Skin Pixels → Calculate Statistics
    │
    ├─→ Average H (Hue)
    ├─→ Average S (Saturation)
    ├─→ Average V (Brightness)
    └─→ Std Dev V (Consistency)
         │
         ▼
    Calculate Scores
         │
         ├─→ Light Score (70% V + 20% S + 10% consistency)
         ├─→ Medium Score (70% V + 20% S + 10% consistency)
         └─→ Dark Score (70% V + 20% S + 10% consistency)
         │
         ▼
    Select Maximum Score
         │
         ▼
    Calculate Confidence
         │
         ├─→ Score margin (difference between top 2)
         ├─→ Consistency factor
         └─→ Final confidence (0-100%)
         │
         ▼
    Return: Tone + Confidence
```

---

## Data Flow

```
Input Image (JPG/PNG)
    │
    ├─→ OpenCV: Load image
    │
    ├─→ Haar Cascade: Detect face
    │   └─→ Face region (x, y, width, height)
    │
    ├─→ Crop face region
    │   └─→ Face image (BGR)
    │
    ├─→ Convert: BGR → RGB
    │   └─→ RGB image
    │
    ├─→ Convert: RGB → HSV
    │   └─→ HSV pixels
    │
    ├─→ Load model: skin_classifier.pkl
    │   └─→ Trained Logistic Regression
    │
    ├─→ Predict: Skin/Non-skin for each pixel
    │   └─→ Binary predictions
    │
    ├─→ Filter: Keep skin pixels only
    │   └─→ Skin pixels array
    │
    ├─→ Calculate: HSV statistics
    │   ├─→ avg_h, avg_s, avg_v
    │   └─→ std_v
    │
    ├─→ Classify: Multi-feature scoring
    │   └─→ Light/Medium/Dark
    │
    └─→ Output: Results + Visualization
        ├─→ Console output
        ├─→ CSV file
        └─→ OpenCV windows
```

---

## Key Components

### 1. Face Detection Module
- **Input:** Full image
- **Output:** Face region coordinates
- **Method:** OpenCV Haar Cascade

### 2. Skin Extraction Module
- **Input:** Face region image
- **Output:** Skin pixels array
- **Method:** Trained ML model (Logistic Regression)

### 3. Classification Module
- **Input:** Skin pixels array
- **Output:** Skin tone + confidence
- **Method:** Multi-feature weighted scoring

---

## File Dependencies

```
skin_tone_detector.py
    │
    ├─→ models/skin_classifier.pkl (trained model)
    ├─→ cv2 (OpenCV - face detection)
    ├─→ numpy (array operations)
    ├─→ pandas (DataFrame for model input)
    └─→ pickle (load trained model)
```

---

## Execution Flow

```
1. Initialize SkinToneDetector
   └─→ Load model from models/skin_classifier.pkl
   └─→ Initialize Haar Cascade

2. Process Image
   ├─→ Load image file
   ├─→ Detect face
   ├─→ Extract skin pixels
   └─→ Classify skin tone

3. Display Results
   ├─→ Print to console
   ├─→ Show visualization
   └─→ Save to CSV (if batch mode)
```

---

## Error Handling

```
┌─────────────────┐
│  Load Image     │──→ Error? → "Could not load image"
└────────┬────────┘
         │
┌────────▼────────┐
│  Detect Face   │──→ Error? → "No face detected"
└────────┬────────┘
         │
┌────────▼────────┐
│ Extract Skin    │──→ Error? → "No skin pixels found"
└────────┬────────┘
         │
┌────────▼────────┐
│  Classify       │──→ Success → Return result
└─────────────────┘
```

---

This workflow diagram shows the complete process from input image to final classification result.
