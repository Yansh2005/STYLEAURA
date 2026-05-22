# ML-Based Clothing Recommendation System
## Phase 1: Skin Tone Detection

A machine learning project that detects faces in images, extracts skin pixels using a trained ML model, and classifies skin tone into Light/Medium/Dark categories.

---

## 🚀 Quick Start

### Installation
```bash
pip install -r requiremnets.txt
```

### Usage

**Single Image:**
```bash
python src/skin_tone_detector.py
```

**Batch Testing:**
```bash
python src/test_multiple_images.py
```

---

## 📋 Project Overview

This project implements a complete skin tone detection pipeline:

1. **Face Detection** - Detects faces using OpenCV Haar Cascade
2. **Skin Extraction** - Uses trained Logistic Regression model to identify skin pixels
3. **Tone Classification** - Classifies skin tone as Light/Medium/Dark using multi-feature analysis

---

## 📁 Project Structure

```
skin-tone-detection/
├── dataset/              # Training dataset
├── models/               # Trained ML model
├── src/                  # Source code
├── test_images/          # Test images
├── notebooks/            # Jupyter notebooks
└── test_results.csv      # Test results
```

---

## 🎯 Results

- **Success Rate:** 100% (all test images processed)
- **Confidence:** 30-100% (improved from 11-63%)
- **Features:** Multi-feature analysis (H, S, V)

---

## 📚 Documentation

- **`PROJECT_SUMMARY.md`** - Complete project overview
- **`USAGE.md`** - Detailed usage guide
- **`ACCURACY_IMPROVEMENTS.md`** - Improvement results
- **`NEXT_STEPS.md`** - Future work guide

---

## 🛠️ Technology Stack

- Python 3.x
- OpenCV (Computer Vision)
- scikit-learn (Machine Learning)
- NumPy, Pandas (Data Processing)

---

## 📊 Test Results

| Image | Skin Tone | Confidence |
|-------|-----------|------------|
| face1.jpg | Light | 30.95% |
| face2.jpg | Dark | 100.00% |
| face3.jpg | Light | 99.51% |

---

## 🎓 For Students

This is a college-level ML project demonstrating:
- Computer Vision (face detection, image processing)
- Machine Learning (classification, feature engineering)
- Software Engineering (modular design, error handling)

---

## 📝 License

Educational Project - For Academic Use

---

## 👤 Author

College ML Project - Skin Tone Detection Module

---

**Status:** ✅ Phase 1 Complete  
**Next:** Phase 2 - Clothing Recommendations
