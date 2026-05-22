# StyleAura — AI-Powered Personal Fashion Advisor
## Complete Project Documentation

---

## 1. Project Overview

**StyleAura** is a full-stack AI-powered web application that provides **personalized fashion recommendations** based on a user's physical attributes. Users upload a photo, and the system uses **Machine Learning** to:

1. **Detect Skin Tone** — Classifies as Light, Medium, or Dark using a trained ML model
2. **Detect Body Shape** — Identifies body shape (Rectangle, Triangle, Inverted Triangle, Hourglass, Oval) using MediaPipe Pose Landmarks
3. **Detect Gender** — Uses DeepFace for face-based gender detection with body-ratio fallback
4. **Generate Recommendations** — Produces gender-aware outfit sets, curated color palettes, and shopping links

> [!IMPORTANT]
> StyleAura combines **3 ML models** (Skin Classifier, MediaPipe Pose, DeepFace) to deliver end-to-end personalized fashion advice — from photo upload to shopping links — in under 15 seconds.

---

## 2. Technology Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.13 | Core backend language |
| **Flask** | 2.3.3 | REST API web framework |
| **Flask-JWT-Extended** | 4.5.3 | JWT authentication (access + refresh tokens) |
| **Flask-CORS** | 4.0.0 | Cross-origin resource sharing |
| **MongoDB** (via PyMongo) | 4.5.0 | Primary database (Atlas cloud) |
| **bcrypt** | 4.0.1 | Password hashing |
| **OpenCV** | ≥4.8.0 | Image processing, face detection (Haar Cascade) |
| **MediaPipe** | ≥0.10.0 | Body pose landmark detection |
| **DeepFace** | ≥0.0.89 | Gender detection from face |
| **scikit-learn** | ≥1.3.0 | Skin tone classification (ML model) |
| **NumPy / Pandas** | ≥1.24 / ≥2.0 | Numerical computation and data handling |
| **SerpAPI** | ≥2.4.2 | Google Shopping product image search |
| **tf-keras** | latest | TensorFlow/Keras backend for DeepFace |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| **React** | 18.3.1 | UI component library |
| **TypeScript** | 5.5.3 | Type-safe JavaScript |
| **Vite** | 5.4.2 | Fast dev server & build tool |
| **TailwindCSS** | 3.4.1 | Utility-first CSS framework |
| **Lucide React** | 0.344.0 | Icon library |

### Database
| Service | Details |
|---|---|
| **MongoDB Atlas** | Cloud-hosted cluster (`cluster0.uqxkaub.mongodb.net`) |
| **Database Name** | `styleaura` |
| **Fallback** | In-memory storage when MongoDB is unavailable |

---

## 3. System Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend (React + Vite — Port 5173)"]
        A[Home Page] --> B[Image Upload]
        B --> C[Analysis Result]
        C --> D[Outfit Recommendations]
        E[Dashboard] --> C
        F[Login/Signup]
        G[About / Contact]
    end

    subgraph Backend["Backend (Flask — Port 5000)"]
        H[Auth Routes]
        I[Image Routes]
        J[ML Analysis Route]
        K[Outfit Images Route]
        L[Chat Route]
        M[Contact Route]
        N[Analysis/Recommendations Routes]
    end

    subgraph ML["ML Pipeline"]
        O[Skin Tone Detector<br/>OpenCV + sklearn]
        P[Body Shape Detector<br/>MediaPipe Pose]
        Q[Gender Detector<br/>DeepFace]
        R[Recommendation Engine<br/>Rule-based]
    end

    subgraph DB["Database"]
        S[(MongoDB Atlas)]
        T[Users Collection]
        U[Images Collection]
        V[Analyses Collection]
        W[Contact Messages]
    end

    B -->|POST /api/images/upload| I
    B -->|POST /api/ml/analyze/:id| J
    J --> O & P & Q
    O & P & Q --> R
    R -->|JSON Response| C
    D -->|GET /api/ml/outfit-images| K
    K -->|SerpAPI / Fallback| D
    F -->|POST /api/auth/login signup| H
    H --> S
    I --> S
    J --> S
```

---

## 4. ML Pipeline — Detailed Explanation

### 4.1 Skin Tone Detection (`ml_src/skin_tone_detector.py`)

**Class:** `SkinToneDetector`

#### Pipeline Steps:
1. **Load Image** — `cv2.imread()` reads the uploaded photo
2. **Face Detection** — OpenCV Haar Cascade (`haarcascade_frontalface_default.xml`)
   - Primary: `scaleFactor=1.05, minNeighbors=3, minSize=(20,20)`
   - Fallback: `scaleFactor=1.1, minNeighbors=1, minSize=(15,15)`
   - Last resort: Upper-center crop (top 45%, middle 60%) as skin sample
3. **Skin Pixel Extraction** — Pre-trained sklearn model (`skin_classifier.pkl`)
   - Converts face region RGB → HSV color space
   - Predicts skin vs non-skin pixels using the ML model
   - Label 1 = skin, Label 2 = non-skin
4. **Skin Tone Classification** — Multi-feature weighted scoring:

| Feature | Weight | Details |
|---|---|---|
| Brightness (V) | 70% | Light: V>175, Medium: 90≤V≤190, Dark: V<110 |
| Saturation (S) | 20% | Boosts the leading category |
| Consistency (std) | 10% | Lower std = higher confidence |

**Output:** `{ skin_tone: "Light"|"Medium"|"Dark", confidence: 0-1, num_skin_pixels: int }`

#### Validation Gates:
- Minimum **50 skin pixels** required, otherwise rejects as non-human image
- Face detection returns a `face_detected` boolean flag

---

### 4.2 Body Shape Detection (`ml_src/body_shape_detector.py`)

**Class:** `BodyShapeDetector`

#### Pipeline Steps:
1. **Load Image** — OpenCV reads and converts BGR → RGB
2. **Pose Detection** — MediaPipe `PoseLandmarker` (model: `pose_landmarker_full.task`, 9.3 MB)
   - Detects 33 body landmarks (shoulders, hips, knees, etc.)
3. **Measurement Extraction:**
   - **Shoulder Width** = distance between landmarks 11 (left shoulder) and 12 (right shoulder)
   - **Hip Width** = distance between landmarks 23 (left hip) and 24 (right hip)
   - **Shoulder-Hip Ratio** = shoulder_width / hip_width
   - **Waist Estimate** = hip_width × 0.75 (hourglass) or × 0.9 (others)

4. **Body Shape Classification:**

| Ratio Range | Body Shape |
|---|---|
| > 1.85 | Inverted Triangle |
| < 1.62 | Triangle |
| 1.62 – 1.72 | Hourglass |
| 1.72 – 1.80 | Rectangle |
| 1.80 – 1.85 | Oval |

5. **Fallback (No Pose Detected):**
   - Checks for face using DeepFace + OpenCV Haar Cascade
   - If face found: defaults to Hourglass (Female) or Rectangle (Male)
   - If no face found by either method: rejects as non-human image

**Output:** `{ body_shape, detected_gender, gender_confidence, pose_detected, measurements }`

---

### 4.3 Gender Detection (`detect_gender()`)

**Primary Method:** DeepFace library
- Uses `DeepFace.analyze(actions=['gender'], enforce_detection=False)`
- Returns Man/Woman scores (0-100)
- Threshold: higher score wins

**Fallback Method:** Shoulder-Hip Ratio Heuristic
| Ratio | Gender | Confidence |
|---|---|---|
| > 1.78 | Male | 0.5 + (ratio - 1.78) × 2 |
| < 1.65 | Female | 0.5 + (1.65 - ratio) × 2 |
| 1.65 – 1.78 | Female (default) | 0.5 |

---

### 4.4 Recommendation Engine

**Function:** `get_full_outfit_recommendations(skin_tone, body_shape, gender)`

Generates complete outfit sets with:
- **Title & Description** — e.g., "Classic Business Suit"
- **Items List** — 4-5 clothing items per outfit
- **Occasion** — Casual, Work, Formal, Party
- **Season** — All Season, Spring/Summer, Autumn/Winter
- **Price** — Estimated price in INR (₹)
- **Rating** — 4.0-5.0 scale
- **Shopping Keywords** — For Google Shopping search

**Database:** 15 outfits per body shape × 5 shapes × 2 genders = **150 unique outfit combinations**

#### Color Palette Generation (`get_color_palette()`)
Returns 6 curated color swatches per skin tone:

| Skin Tone | Sample Colors |
|---|---|
| Light | Emerald Green, Navy Blue, Ruby Red, Plum Purple, Blush Pink, Charcoal |
| Medium | Olive Green, Mustard Yellow, Coral, Teal, Warm Beige, Terracotta |
| Dark | Bright Yellow, Cobalt Blue, Lavender, Vibrant Red, Ivory White, Hot Pink |

---

## 5. REST API Endpoints

### 5.1 Authentication (`/api/auth`)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/signup` | ❌ | Register new user (email, password, first_name, last_name) |
| POST | `/login` | ❌ | Login with email/password → returns JWT tokens |
| POST | `/refresh` | 🔄 Refresh | Get new access token using refresh token |
| GET | `/me` | ✅ JWT | Get current logged-in user profile |
| PUT | `/update-profile` | ✅ JWT | Update user profile fields |

**JWT Configuration:**
- Access Token Expiry: **24 hours**
- Refresh Token Expiry: **30 days**
- Passwords hashed with **bcrypt**

---

### 5.2 Images (`/api/images`)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/upload` | ✅ JWT | Upload image (multipart form, field: `image`) |
| GET | `/` | ✅ JWT | List user's images (paginated: `?page=1&per_page=10`) |
| GET | `/:id` | ✅ JWT | Get image metadata by ID |
| GET | `/:id/file` | ✅ JWT | Serve actual image file |
| DELETE | `/:id` | ✅ JWT | Delete image from filesystem + database |

**Upload Configuration:**
- Max file size: **16 MB**
- Allowed formats: PNG, JPG, JPEG, WEBP
- Files stored in: `backend/uploads/` with UUID filenames

---

### 5.3 ML Analysis (`/api/ml`)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/analyze/:image_id` | ✅ JWT | Run full ML pipeline on uploaded image |
| POST | `/analyze-direct` | ❌ | Direct upload + analysis (no DB save) |
| GET | `/outfit-images?q=...&n=3` | ❌ | Search product images via SerpAPI |

#### `/analyze/:image_id` Response:
```json
{
  "message": "Analysis complete",
  "analysis": {
    "skin_tone": "Medium",
    "body_shape": "Triangle",
    "confidence_score": 0.89,
    "detected_gender": "Female",
    "gender_confidence": 0.92,
    "body_measurements": {
      "shoulder_width_norm": 0.18,
      "hip_width_norm": 0.12,
      "waist_width_est": 0.108,
      "shoulder_hip_ratio": 1.58
    },
    "color_palette": [...]
  },
  "recommendations": {
    "outfits": [...],
    "styles": [...],
    "colors": [...],
    "color_palette": [...],
    "gender": "Female"
  }
}
```

---

### 5.4 Analysis History (`/api/analysis`)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/` | ✅ JWT | List user's analyses (paginated) |
| GET | `/:id` | ✅ JWT | Get specific analysis |
| DELETE | `/:id` | ✅ JWT | Delete an analysis |

### 5.5 Chat (`/api/chat`)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/message` | ✅ JWT | Send message to keyword-based chatbot |
| GET | `/history` | ✅ JWT | Get chat history (placeholder) |

The chatbot uses **keyword matching** to respond to queries about: pricing, how-it-works, recommendations, contact info, shipping, returns, account, security, accuracy, styles, sizes, and brands.

### 5.6 Contact (`/api/contact`)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/` | ❌ | Submit contact message (name, email, subject, message) |
| GET | `/` | ❌ | Retrieve all contact messages (admin) |

Messages are stored in MongoDB's `contact_messages` collection.

---

## 6. Database Schema (MongoDB)

### 6.1 `users` Collection
```json
{
  "_id": "ObjectId",
  "email": "string (unique, indexed)",
  "password_hash": "string (bcrypt)",
  "first_name": "string",
  "last_name": "string",
  "created_at": "datetime (UTC)",
  "updated_at": "datetime (UTC)"
}
```

### 6.2 `user_images` Collection
```json
{
  "_id": "ObjectId",
  "id": "int (surrogate numeric ID)",
  "user_id": "string (references users._id)",
  "filename": "string (UUID-based)",
  "file_path": "string (absolute server path)",
  "uploaded_at": "datetime (UTC)"
}
```

### 6.3 `analyses` Collection
```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "image_id": "int",
  "skin_tone": "Light | Medium | Dark",
  "body_shape": "Rectangle | Triangle | Inverted Triangle | Hourglass | Oval",
  "confidence_score": "float (0-1)",
  "detected_gender": "Male | Female",
  "gender_confidence": "float (0-1)",
  "body_measurements": {
    "shoulder_width_norm": "float",
    "hip_width_norm": "float",
    "waist_width_est": "float",
    "shoulder_hip_ratio": "float"
  },
  "color_palette": "[{name, hex, description}]",
  "created_at": "datetime (UTC)"
}
```

### 6.4 `contact_messages` Collection
```json
{
  "_id": "ObjectId",
  "name": "string",
  "email": "string",
  "subject": "string",
  "message": "string",
  "status": "new",
  "created_at": "datetime (UTC)"
}
```

### Database Indexes
- `users.email` — unique index
- `user_images.(user_id, uploaded_at)` — compound descending
- `analyses.(user_id, created_at)` — compound descending
- `contact_messages.(created_at)` — descending

---

## 7. Frontend Pages & Components

### 7.1 Pages (9 total)

| Page | File | Description |
|---|---|---|
| **Home** | `Home.tsx` | Hero section, video showcase, how-it-works steps, features grid, CTA |
| **Login** | `Login.tsx` | Email/password login form with JWT token storage |
| **Signup** | `Signup.tsx` | Registration form with validation (name, email, password) |
| **Image Upload** | `ImageUpload.tsx` | Drag-and-drop + file picker, 5-step progress animation during analysis |
| **Analysis Result** | `AnalysisResult.tsx` | Displays body shape, skin tone, gender, confidence score, color palette, style tips |
| **Outfit Recommendations** | `OutfitRecommendations.tsx` | Filterable outfit cards with product images, shopping links, favorites |
| **Dashboard** | `Dashboard.tsx` | User profile, stats, analysis history with relative timestamps |
| **About** | `About.tsx` | Mission, values, story, stats |
| **Contact** | `Contact.tsx` | Contact form (saved to MongoDB), contact info cards |

### 7.2 Shared Components (2)
| Component | File | Description |
|---|---|---|
| **Navigation** | `Navigation.tsx` | Responsive navbar with mobile hamburger menu, auth-aware links |
| **Footer** | `Footer.tsx` | Site links, branding, copyright |

### 7.3 Key UI Features
- **Circular Progress Ring** — Animated SVG confidence score display
- **Product Image Carousel** — Dots navigation with hover-reveal price/source overlay
- **5-Step Analysis Progress** — Real-time step indicators during ML processing
- **Staggered Animations** — CSS `stagger-children` for sequential card reveals
- **Glassmorphism Effects** — Frosted glass backgrounds on hero badges
- **Responsive Design** — Full mobile → desktop adaptation via Tailwind breakpoints

---

## 8. Complete Application Flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend as React Frontend
    participant Backend as Flask Backend
    participant ML as ML Pipeline
    participant DB as MongoDB
    participant Shop as SerpAPI

    User->>Frontend: Opens StyleAura (localhost:5173)
    User->>Frontend: Clicks "Get Started"
    Frontend->>Frontend: Redirects to Login (if not authenticated)
    User->>Frontend: Enters credentials
    Frontend->>Backend: POST /api/auth/login
    Backend->>DB: Verify user + bcrypt check
    DB-->>Backend: User found
    Backend-->>Frontend: JWT access_token + refresh_token
    Frontend->>Frontend: Stores tokens in localStorage

    User->>Frontend: Navigates to Upload page
    User->>Frontend: Selects/drops a photo
    Frontend->>Frontend: Shows image preview
    User->>Frontend: Clicks "Analyze My Style"
    Frontend->>Backend: POST /api/images/upload (multipart)
    Backend->>DB: Save image metadata
    Backend-->>Frontend: { image: { id: 123 } }

    Frontend->>Backend: POST /api/ml/analyze/123
    Backend->>ML: Step 1 — Skin Tone Detection
    ML->>ML: Haar Cascade face detect
    ML->>ML: sklearn skin pixel extraction
    ML->>ML: HSV-based tone classification
    ML-->>Backend: { skin_tone: "Medium", confidence: 0.89 }

    Backend->>ML: Step 2 — Body Shape Detection
    ML->>ML: MediaPipe pose landmark detection
    ML->>ML: Shoulder/hip ratio calculation
    ML->>ML: Shape classification
    ML-->>Backend: { body_shape: "Triangle", measurements: {...} }

    Backend->>ML: Step 3 — Gender Detection
    ML->>ML: DeepFace gender analysis
    ML-->>Backend: { gender: "Female", confidence: 0.92 }

    Backend->>ML: Step 4 — Generate Recommendations
    ML-->>Backend: 15 outfit sets + color palette

    Backend->>DB: Save analysis record
    Backend-->>Frontend: Full analysis + recommendations JSON

    Frontend->>Frontend: Navigate to Analysis Result page
    Frontend->>Frontend: Display body shape, skin tone, colors, tips
    User->>Frontend: Clicks "View Outfit Recommendations"
    Frontend->>Frontend: Navigate to Recommendations page

    loop For each outfit card
        Frontend->>Backend: GET /api/ml/outfit-images?q=keywords
        Backend->>Shop: SerpAPI Google Shopping search
        Shop-->>Backend: Product images + prices
        Backend-->>Frontend: Image carousel data
    end

    User->>Frontend: Clicks "Shop on Google"
    Frontend->>Frontend: Opens Google Shopping in new tab
```

---

## 9. Project File Structure

```
STYLEAURA_1/
├── Styleaura/
│   ├── backend/                          # Flask Backend
│   │   ├── app.py                        # Flask app factory, blueprint registration
│   │   ├── run.py                        # Server entry point (port 5000)
│   │   ├── config.py                     # Configuration (MongoDB URI, JWT, CORS, uploads)
│   │   ├── database.py                   # MongoDB connection, ORM models (User, UserImage, Analysis, Recommendation)
│   │   ├── requirements.txt              # Python dependencies
│   │   ├── .env                          # Environment variables (secrets)
│   │   ├── pose_landmarker_full.task      # MediaPipe pose model (9.3 MB)
│   │   │
│   │   ├── ml_models/
│   │   │   └── skin_classifier.pkl       # Trained sklearn skin/non-skin classifier
│   │   │
│   │   ├── ml_src/
│   │   │   ├── skin_tone_detector.py     # Skin tone detection pipeline
│   │   │   └── body_shape_detector.py    # Body shape + gender + recommendations engine
│   │   │
│   │   ├── routes/
│   │   │   ├── auth.py                   # /api/auth — signup, login, refresh, profile
│   │   │   ├── images.py                 # /api/images — upload, list, delete
│   │   │   ├── ml_analysis.py            # /api/ml/analyze — ML pipeline orchestrator
│   │   │   ├── outfit_images.py          # /api/ml/outfit-images — product image search
│   │   │   ├── analysis.py               # /api/analysis — CRUD for analysis history
│   │   │   ├── recommendations.py        # /api/recommendations — CRUD for recommendations
│   │   │   ├── chat.py                   # /api/chat — keyword-based chatbot
│   │   │   ├── contact.py                # /api/contact — contact form submissions
│   │   │   ├── cart.py                   # /api/cart — shopping cart (placeholder)
│   │   │   └── users.py                  # /api/users — user management
│   │   │
│   │   ├── utils/
│   │   │   └── validators.py             # Email, password, image file validation
│   │   │
│   │   └── uploads/                      # User-uploaded images (UUID filenames)
│   │
│   └── project/                          # React Frontend
│       ├── index.html                    # HTML entry point
│       ├── package.json                  # Node.js dependencies
│       ├── vite.config.ts                # Vite dev server config
│       ├── tailwind.config.js            # TailwindCSS config
│       ├── tsconfig.json                 # TypeScript config
│       │
│       ├── public/
│       │   ├── styleaura-demo.mp4        # Demo video on home page
│       │   └── outfits/                  # Static outfit images
│       │
│       └── src/
│           ├── App.tsx                   # Main app — routing, state management, auth
│           ├── main.tsx                  # React DOM entry point
│           ├── index.css                 # Global styles, animations, design system
│           ├── components/
│           │   ├── Navigation.tsx         # Responsive navbar
│           │   └── Footer.tsx            # Site footer
│           └── pages/
│               ├── Home.tsx              # Landing page with video
│               ├── Login.tsx             # Login form
│               ├── Signup.tsx            # Registration form
│               ├── ImageUpload.tsx       # Photo upload + analysis trigger
│               ├── AnalysisResult.tsx    # ML results display
│               ├── OutfitRecommendations.tsx  # Outfit cards with filters
│               ├── Dashboard.tsx         # User dashboard + history
│               ├── About.tsx             # About page
│               └── Contact.tsx           # Contact form
│
└── WhatsApp Video 2026-04-25 at 10.21.21 AM.mp4  # Original demo video
```

---

## 10. Security Features

| Feature | Implementation |
|---|---|
| **Password Hashing** | bcrypt with auto-generated salt |
| **JWT Authentication** | Access tokens (24h) + refresh tokens (30d) |
| **Protected Routes** | `@jwt_required()` decorator on sensitive endpoints |
| **Frontend Route Guard** | Redirects unauthenticated users to login page |
| **CORS Restriction** | Only `localhost:5173` and `127.0.0.1:5173` allowed |
| **File Validation** | Type check (image/*), size limit (16 MB), allowed extensions |
| **Input Validation** | Email format, password strength (min 8 chars), required fields |
| **UUID Filenames** | Uploaded files renamed to prevent path traversal |
| **Temp File Cleanup** | Direct-analyze endpoint cleans up temp files in `finally` block |

---

## 11. How to Run the Project

### Prerequisites
- Python 3.10+ installed
- Node.js 18+ installed
- MongoDB Atlas account (or local MongoDB)

### Backend Setup
```bash
cd Styleaura/backend
pip install -r requirements.txt
python run.py
# Server starts on http://localhost:5000
```

### Frontend Setup
```bash
cd Styleaura/project
npm install
npm run dev
# Dev server starts on http://localhost:5173
```

### Environment Variables (`.env`)
```
MONGO_URI=mongodb+srv://styleaura:styleaura@cluster0.uqxkaub.mongodb.net/
MONGO_DB_NAME=styleaura
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=jwt-secret-string
SERPAPI_KEY=your-serpapi-key  # Optional — for real product images
```

---

## 12. Key Technical Decisions

| Decision | Rationale |
|---|---|
| **Sequential ML execution** | Skin tone → Body shape runs sequentially (not parallel) to avoid OOM on low-RAM systems |
| **Manual garbage collection** | `gc.collect()` called between ML stages to free intermediate memory |
| **In-memory fallback** | App remains functional even without MongoDB — data stored in Python dicts/lists |
| **24-hour image cache** | SerpAPI results cached in-memory to reduce API calls |
| **Unsplash fallback images** | Curated fallback when SerpAPI key is not configured |
| **Session storage for analysis** | Analysis data persisted in `sessionStorage` to survive page navigation |
| **Photo in state only** | Base64 photo kept in React state (not sessionStorage) to avoid quota limits |
| **UTC timestamps with Z suffix** | Backend appends `Z` to ISO timestamps so JS correctly parses as UTC |

---

## 13. Future Enhancements

- Email notifications for contact form submissions (SMTP integration)
- Chat history persistence in MongoDB
- Admin dashboard for managing users and contact messages
- More granular skin tone categories (6+ levels)
- Integration with additional shopping APIs (Amazon, Myntra)
- User feedback loop to improve ML accuracy over time
- PWA support for mobile installation

---

> **Project:** StyleAura — AI-Powered Personal Fashion Advisor
> **Institution:** CHARUSAT University, Vadodara, Gujarat
> **Contact:** 23dcs120@charusat.edu.in
