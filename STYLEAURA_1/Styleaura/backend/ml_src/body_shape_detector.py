import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

# ── Gender Detection via DeepFace ──────────────────────────────────────────────
_deepface_available = False
try:
    from deepface import DeepFace
    _deepface_available = True
except ImportError:
    logger.warning("DeepFace not installed — gender detection will use body-ratio fallback.")


def detect_gender(image_path):
    """
    Detect gender from a face image using DeepFace.
    Returns 'Male' or 'Female' with a confidence score.
    Falls back to None if detection fails.
    """
    if not _deepface_available:
        return None, 0.0

    try:
        results = DeepFace.analyze(
            img_path=image_path,
            actions=['gender'],
            enforce_detection=False,
            silent=True
        )
        if isinstance(results, list):
            results = results[0]

        gender_data = results.get('gender', {})
        man_score = gender_data.get('Man', 0)
        woman_score = gender_data.get('Woman', 0)

        if man_score > woman_score:
            return 'Male', float(man_score / 100.0)
        else:
            return 'Female', float(woman_score / 100.0)
    except Exception as e:
        logger.warning(f"DeepFace gender detection failed: {e}")
        return None, 0.0


# ── Body Shape Detection ──────────────────────────────────────────────────────

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
            # Read with OpenCV first (handles all formats + Windows paths reliably)
            bgr_image = cv2.imread(image_path_or_array)
            if bgr_image is None:
                raise ValueError(f"Failed to load image from file: {image_path_or_array}")
            image_rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            file_path = image_path_or_array
        else:
            image_rgb = cv2.cvtColor(image_path_or_array, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            file_path = None

        results = self.detector.detect(mp_image)
        
        if not results.pose_landmarks or len(results.pose_landmarks) == 0:
            # No body pose found — check if a human is present using two independent methods:
            # 1. DeepFace (if model weights available), 2. OpenCV Haar cascade as fallback.
            logger.warning("No pose landmarks detected — checking for human presence via face detection.")

            detected_gender = None
            gender_confidence = 0.0
            deepface_failed = False

            if file_path:
                detected_gender, gender_confidence = detect_gender(file_path)
                if detected_gender is None:
                    deepface_failed = True

            # --- OpenCV Haar Cascade as independent backup ---
            opencv_face_found = False
            try:
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                face_cascade = cv2.CascadeClassifier(cascade_path)
                bgr_check = cv2.imread(file_path) if file_path else image_rgb
                if bgr_check is not None:
                    gray_check = cv2.cvtColor(bgr_check, cv2.COLOR_BGR2GRAY)
                    faces_check = face_cascade.detectMultiScale(
                        gray_check, scaleFactor=1.05, minNeighbors=3, minSize=(20, 20)
                    )
                    if len(faces_check) == 0:
                        # Try more permissive settings
                        faces_check = face_cascade.detectMultiScale(
                            gray_check, scaleFactor=1.1, minNeighbors=1, minSize=(15, 15)
                        )
                    opencv_face_found = len(faces_check) > 0
                    if opencv_face_found:
                        logger.info(f"OpenCV Haar cascade detected {len(faces_check)} face(s).")
            except Exception as cv_err:
                logger.warning(f"OpenCV face check failed: {cv_err}")

            # VALIDATION GATE:
            # - If DeepFace succeeded and has high confidence → trust it (allow)
            # - If DeepFace failed/offline → trust OpenCV result
            # - Only reject if BOTH DeepFace AND OpenCV find no human
            deepface_confident = (detected_gender is not None and gender_confidence >= 0.60)

            if not deepface_confident and not opencv_face_found:
                raise ValueError(
                    "No human body or face detected in the image. "
                    "Please upload a clear full-body or portrait photo of a person."
                )

            # Human face WAS detected (by at least one method), but no full-body pose.
            # Use gender from DeepFace if available, else default.
            if detected_gender is None:
                detected_gender = 'Female'
                gender_confidence = 0.5
            logger.warning(f"No pose but human face detected (gender={detected_gender}, conf={gender_confidence:.2f}). Using default shape.")
            default_shape = "Hourglass" if detected_gender == 'Female' else "Rectangle"
            return {
                "body_shape": default_shape,
                "detected_gender": detected_gender,
                "gender_confidence": round(gender_confidence, 3),
                "pose_detected": False,
                "measurements": {
                    "shoulder_width_norm": 0.0,
                    "hip_width_norm": 0.0,
                    "waist_width_est": 0.0,
                    "shoulder_hip_ratio": 0.0
                }
            }
            
        landmarks = results.pose_landmarks[0]
        
        def dist(lm1, lm2):
            return np.sqrt((lm1.x - lm2.x)**2 + (lm1.y - lm2.y)**2 + (lm1.z - lm2.z)**2)
            
        shoulder_width = dist(landmarks[11], landmarks[12])
        hip_width = dist(landmarks[23], landmarks[24])
        
        # Avoid division by zero
        if hip_width == 0:
            hip_width = 0.001

        # Calculate ratio
        ratio = shoulder_width / hip_width
        
        shape = "Rectangle"
        if ratio > 1.85:
            shape = "Inverted Triangle"
        elif ratio < 1.62:
            shape = "Triangle"
        elif 1.62 <= ratio <= 1.72:
            shape = "Hourglass"
        elif 1.72 < ratio <= 1.85:
            shape = "Oval" if ratio > 1.8 else "Rectangle"

        waist_width_est = hip_width * 0.75 if shape == "Hourglass" else hip_width * 0.9

        # ── Gender detection ──
        detected_gender = None
        gender_confidence = 0.0

        # Primary: DeepFace face-based gender detection
        if file_path:
            detected_gender, gender_confidence = detect_gender(file_path)

        # Fallback: Use shoulder-hip ratio heuristic
        if detected_gender is None:
            if ratio > 1.78:
                detected_gender = 'Male'
                gender_confidence = min(0.85, 0.5 + (ratio - 1.78) * 2)
            elif ratio < 1.65:
                detected_gender = 'Female'
                gender_confidence = min(0.85, 0.5 + (1.65 - ratio) * 2)
            else:
                # Ambiguous zone — default to Female for safety
                detected_gender = 'Female'
                gender_confidence = 0.5

        return {
            "body_shape": shape,
            "detected_gender": detected_gender,
            "gender_confidence": round(gender_confidence, 3),
            "pose_detected": True,
            "measurements": {
                "shoulder_width_norm": float(shoulder_width),
                "hip_width_norm": float(hip_width),
                "waist_width_est": float(waist_width_est),
                "shoulder_hip_ratio": float(ratio)
            }
        }


# ── Color Palettes ────────────────────────────────────────────────────────────

def get_color_palette(skin_tone):
    """
    Return a list of recommended color swatches (name + hex) based on detected skin tone.
    """
    palettes = {
        "Light": [
            {"name": "Emerald Green", "hex": "#50C878", "description": "Rich jewel tone that complements fair skin"},
            {"name": "Navy Blue", "hex": "#000080", "description": "Classic deep blue for elegant contrast"},
            {"name": "Ruby Red", "hex": "#9B111E", "description": "Bold jewel tone for striking outfits"},
            {"name": "Plum Purple", "hex": "#8E4585", "description": "Deep berry shade for a luxurious look"},
            {"name": "Blush Pink", "hex": "#DE5D83", "description": "Soft warm pink that flatters light tones"},
            {"name": "Charcoal", "hex": "#36454F", "description": "Sophisticated neutral for any occasion"}
        ],
        "Medium": [
            {"name": "Olive Green", "hex": "#808000", "description": "Earthy tone that enhances warm undertones"},
            {"name": "Mustard Yellow", "hex": "#FFDB58", "description": "Warm golden shade for a vibrant look"},
            {"name": "Coral", "hex": "#FF7F50", "description": "Warm peachy-orange that brightens skin"},
            {"name": "Teal", "hex": "#008080", "description": "Rich blue-green for elegant contrast"},
            {"name": "Warm Beige", "hex": "#F5DEB3", "description": "Natural complement to medium tones"},
            {"name": "Terracotta", "hex": "#E2725B", "description": "Earthy warm red for casual sophistication"}
        ],
        "Dark": [
            {"name": "Bright Yellow", "hex": "#FFD700", "description": "Vibrant gold that pops beautifully"},
            {"name": "Cobalt Blue", "hex": "#0047AB", "description": "Intense blue for a bold statement"},
            {"name": "Lavender", "hex": "#E6E6FA", "description": "Soft pastel for stunning contrast"},
            {"name": "Vibrant Red", "hex": "#FF0000", "description": "Classic bold red for maximum impact"},
            {"name": "Ivory White", "hex": "#FFFFF0", "description": "Clean white that creates sharp elegance"},
            {"name": "Hot Pink", "hex": "#FF69B4", "description": "Energetic pink for lively outfits"}
        ]
    }
    return palettes.get(skin_tone, palettes["Medium"])


# ── Outfit Recommendations (simple) ──────────────────────────────────────────

def get_outfit_recommendations(skin_tone, body_shape, gender='Female'):
    """
    Given a skin tone, body shape, and gender, return suitable clothing styles and colors.
    """
    recommendation = {
        "styles": [],
        "colors": [],
        "summary": ""
    }

    # Body shape → style mapping (gender-specific)
    if gender == 'Male':
        shape_styles = {
            "Rectangle": ["Layered outfits", "Structured blazers", "Patterned shirts", "Slim-fit trousers"],
            "Triangle": ["V-neck T-shirts", "Structured shoulder jackets", "Dark-wash jeans", "Fitted polos"],
            "Inverted Triangle": ["Straight-leg pants", "V-neck sweaters", "Simple crew-neck tees", "Chinos"],
            "Hourglass": ["Fitted button-downs", "Tailored suits", "Slim-fit jeans", "V-neck cardigans"],
            "Oval": ["Vertical stripe shirts", "Dark solid colors", "Structured blazers", "Straight-cut trousers"]
        }
    else:
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

    gender_word = "men's" if gender == 'Male' else "women's"
    recommendation["summary"] = (
        f"Based on your unique features, we recommend {gender_word} styles like "
        f"{', '.join(recommendation['styles'])} in colors such as {', '.join(recommendation['colors'])}."
    )

    return recommendation


# ── Full Outfit Recommendations (gender-aware) ──────────────────────────────

def get_full_outfit_recommendations(skin_tone, body_shape, gender='Female'):
    """
    Generate complete outfit sets based on detected skin tone, body shape, AND gender.
    Each outfit has items, colors, occasion, season, price, and shopping keywords.
    """
    base = get_outfit_recommendations(skin_tone, body_shape, gender)
    palette = get_color_palette(skin_tone)

    if gender == 'Male':
        outfits = _get_male_outfits(body_shape)
    else:
        outfits = _get_female_outfits(body_shape)

    # Attach the color palette to each outfit
    for outfit in outfits:
        outfit["recommended_colors"] = palette[:3]
        outfit["gender"] = gender

    return {
        "styles": base["styles"],
        "colors": base["colors"],
        "color_palette": palette,
        "summary": base["summary"],
        "outfits": outfits,
        "gender": gender
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MALE OUTFITS DATABASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _get_male_outfits(body_shape):
    """Return male outfit recommendations by body shape."""
    shape_outfits = {
        "Rectangle": [
            {
                "title": "Classic Business Suit",
                "description": "Tailored suit with structured shoulders to create a powerful silhouette",
                "items": ["Navy Blue Blazer", "White Dress Shirt", "Slim-Fit Trousers", "Oxford Shoes", "Silk Tie"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹24,999",
                "rating": 4.8,
                "image": "🤵",
                "shopping_keywords": "men navy blue suit blazer formal"
            },
            {
                "title": "Smart Casual Friday",
                "description": "Polished yet relaxed look perfect for the modern workplace",
                "items": ["Structured Blazer", "Slim-Fit Chinos", "Crew-Neck T-Shirt", "Loafers"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹12,499",
                "rating": 4.6,
                "image": "👔",
                "shopping_keywords": "men smart casual blazer chinos"
            },
            {
                "title": "Weekend Explorer",
                "description": "Layered casual outfit that adds dimension to a straight frame",
                "items": ["Bomber Jacket", "Graphic Tee", "Dark Wash Jeans", "White Sneakers"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹8,999",
                "rating": 4.5,
                "image": "🧥",
                "shopping_keywords": "men bomber jacket casual jeans sneakers"
            },
            {
                "title": "Party Night Out",
                "description": "Sharp party wear with textured fabrics for visual interest",
                "items": ["Velvet Blazer", "Black Slim Shirt", "Tailored Trousers", "Chelsea Boots"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹16,999",
                "rating": 4.7,
                "image": "🎩",
                "shopping_keywords": "men party wear velvet blazer black shirt"
            },
            {
                "title": "Athleisure Edge",
                "description": "Modern sporty look with clean lines and technical fabrics",
                "items": ["Tech Joggers", "Performance Hoodie", "Running Shoes", "Sporty Watch"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹7,499",
                "rating": 4.4,
                "image": "🏃",
                "shopping_keywords": "men athleisure joggers hoodie sneakers"
            },
            {
                "title": "Layered Winter Look",
                "description": "Multiple layers create depth and add shape to a rectangle frame",
                "items": ["Wool Overcoat", "Cable-Knit Sweater", "Corduroy Pants", "Leather Boots"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹19,999",
                "rating": 4.7,
                "image": "🧣",
                "shopping_keywords": "men wool overcoat cable knit sweater winter"
            },
            {
                "title": "Printed Shirt Casual",
                "description": "Bold printed shirts break up the straight-line silhouette",
                "items": ["Printed Camp-Collar Shirt", "Slim Shorts", "Canvas Sneakers", "Sunglasses"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹5,999",
                "rating": 4.3,
                "image": "🌴",
                "shopping_keywords": "men printed casual shirt shorts summer"
            },
            {
                "title": "Indian Festive Wear",
                "description": "Traditional kurta with modern styling for celebrations",
                "items": ["Embroidered Kurta", "Churidar Pants", "Mojari Shoes", "Pocket Square"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹14,999",
                "rating": 4.6,
                "image": "🪔",
                "shopping_keywords": "men embroidered kurta festive indian wear"
            },
            {
                "title": "Denim on Denim",
                "description": "Canadian tuxedo styled right for a bold casual statement",
                "items": ["Denim Jacket", "Denim Jeans (Different Wash)", "White T-Shirt", "Boots"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹9,499",
                "rating": 4.4,
                "image": "👖",
                "shopping_keywords": "men denim jacket jeans casual outfit"
            },
            {
                "title": "Formal Evening",
                "description": "Black-tie ready look for galas and formal dinners",
                "items": ["Black Tuxedo Suit", "White Wing-Collar Shirt", "Bow Tie", "Patent Leather Shoes"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹34,999",
                "rating": 4.9,
                "image": "🤵",
                "shopping_keywords": "men tuxedo suit black tie formal evening"
            },
            {
                "title": "Polo Weekend",
                "description": "Clean polo look for weekend brunches and casual get-togethers",
                "items": ["Fitted Polo Shirt", "Tailored Shorts", "Boat Shoes", "Leather Belt"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹6,499",
                "rating": 4.3,
                "image": "👕",
                "shopping_keywords": "men polo shirt tailored shorts boat shoes"
            },
            {
                "title": "Linen Summer",
                "description": "Breezy linen set perfect for hot weather with effortless style",
                "items": ["Linen Shirt", "Linen Trousers", "Leather Sandals", "Straw Hat"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹8,499",
                "rating": 4.5,
                "image": "☀️",
                "shopping_keywords": "men linen shirt trousers summer outfit"
            },
            {
                "title": "Office Power Move",
                "description": "Commanding office presence with well-fitted separates",
                "items": ["Charcoal Blazer", "Light Blue Shirt", "Navy Trousers", "Monk-Strap Shoes"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹18,999",
                "rating": 4.7,
                "image": "💼",
                "shopping_keywords": "men charcoal blazer office wear formal"
            },
            {
                "title": "Streetwear Fresh",
                "description": "Urban streetwear with oversized proportions to add shape",
                "items": ["Oversized Hoodie", "Cargo Pants", "High-Top Sneakers", "Beanie Cap"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹7,999",
                "rating": 4.4,
                "image": "🎒",
                "shopping_keywords": "men streetwear hoodie cargo pants sneakers"
            },
            {
                "title": "Wedding Guest",
                "description": "Elegant outfit for attending weddings and celebrations",
                "items": ["Three-Piece Suit", "Printed Pocket Square", "Cufflinks", "Brogues"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹28,999",
                "rating": 4.8,
                "image": "💎",
                "shopping_keywords": "men three piece suit wedding guest formal"
            }
        ],
        "Triangle": [
            {
                "title": "Broad Shoulder Blazer",
                "description": "Structured shoulders to balance wider hips for a proportional look",
                "items": ["Padded Shoulder Blazer", "Slim-Fit Trousers", "Oxford Shirt", "Derby Shoes"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹16,999",
                "rating": 4.7,
                "image": "💼",
                "shopping_keywords": "men structured blazer slim fit trousers office"
            },
            {
                "title": "Horizontal Stripe Power",
                "description": "Horizontal stripes on top widen the upper body for balance",
                "items": ["Striped Polo Shirt", "Dark Straight Jeans", "White Sneakers", "Aviator Sunglasses"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹6,999",
                "rating": 4.4,
                "image": "👕",
                "shopping_keywords": "men striped polo shirt dark jeans casual"
            },
            {
                "title": "Layered Office Look",
                "description": "Vest and blazer layers build upper body presence",
                "items": ["Fitted Vest", "Button-Down Shirt", "Dark Chinos", "Monk-Strap Shoes"],
                "occasion": "Work",
                "season": "Autumn/Winter",
                "price": "₹14,499",
                "rating": 4.6,
                "image": "👔",
                "shopping_keywords": "men vest blazer layered office formal"
            },
            {
                "title": "Bold Party Look",
                "description": "Statement jacket draws attention upward for evening events",
                "items": ["Embroidered Jacket", "Black Slim Shirt", "Fitted Trousers", "Oxford Shoes"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹18,999",
                "rating": 4.7,
                "image": "🎩",
                "shopping_keywords": "men embroidered jacket party wear formal"
            },
            {
                "title": "Casual Leather Jacket",
                "description": "A leather or faux-leather jacket adds bulk to the upper body",
                "items": ["Leather Jacket", "Plain T-Shirt", "Dark Jeans", "Chelsea Boots"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹12,999",
                "rating": 4.6,
                "image": "🧥",
                "shopping_keywords": "men leather jacket dark jeans boots casual"
            },
            {
                "title": "Formal Suit Balance",
                "description": "Well-padded formal suit to create proportional shoulders",
                "items": ["Charcoal Suit", "White Shirt", "Silk Tie", "Dress Shoes"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹24,999",
                "rating": 4.8,
                "image": "🤵",
                "shopping_keywords": "men charcoal suit formal padded shoulders"
            },
            {
                "title": "Workout Ready",
                "description": "Athletic wear that emphasizes the upper body",
                "items": ["Fitted Tank Top", "Athletic Shorts", "Running Shoes", "Sports Watch"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹5,499",
                "rating": 4.3,
                "image": "🏋️",
                "shopping_keywords": "men athletic wear tank top shorts gym"
            },
            {
                "title": "Puffer Jacket Style",
                "description": "Puffer jacket adds volume on top for a balanced winter look",
                "items": ["Puffer Jacket", "Turtleneck Sweater", "Slim Jeans", "Boots"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹11,999",
                "rating": 4.5,
                "image": "❄️",
                "shopping_keywords": "men puffer jacket turtleneck winter outfit"
            },
            {
                "title": "Button-Down Casual",
                "description": "Relaxed button-down with rolled sleeves for a wider shoulder look",
                "items": ["Oxford Button-Down", "Chino Shorts", "Boat Shoes", "Braided Belt"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹7,499",
                "rating": 4.4,
                "image": "🌊",
                "shopping_keywords": "men oxford button down chino shorts casual"
            },
            {
                "title": "Sherwani Festive",
                "description": "Classic Indian sherwani with broad shoulder styling",
                "items": ["Embroidered Sherwani", "Churidar", "Jutti Shoes", "Turban"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹22,999",
                "rating": 4.8,
                "image": "🪔",
                "shopping_keywords": "men sherwani embroidered festive indian wedding"
            },
            {
                "title": "Double-Breasted Flex",
                "description": "Double-breasted blazer adds visual width to the torso",
                "items": ["Double-Breasted Blazer", "Turtleneck", "Pleated Trousers", "Loafers"],
                "occasion": "Formal",
                "season": "Autumn/Winter",
                "price": "₹20,999",
                "rating": 4.7,
                "image": "🧥",
                "shopping_keywords": "men double breasted blazer turtleneck formal"
            },
            {
                "title": "Varsity Vibes",
                "description": "Varsity jacket with wide shoulders for a youthful balanced look",
                "items": ["Varsity Jacket", "Graphic Tee", "Joggers", "High-Top Sneakers"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹8,999",
                "rating": 4.4,
                "image": "🎒",
                "shopping_keywords": "men varsity jacket joggers casual outfit"
            },
            {
                "title": "Nehru Jacket Elegance",
                "description": "Traditional Nehru jacket adds structure to the upper body",
                "items": ["Nehru Jacket", "Mandarin Collar Shirt", "Slim Trousers", "Mojari"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹13,999",
                "rating": 4.6,
                "image": "🇮🇳",
                "shopping_keywords": "men nehru jacket mandarin collar shirt formal"
            },
            {
                "title": "Sporty Sunday",
                "description": "Clean sporty outfit for relaxed weekends",
                "items": ["Track Jacket", "Slim Joggers", "Running Shoes", "Cap"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹6,999",
                "rating": 4.3,
                "image": "🏃",
                "shopping_keywords": "men track jacket joggers sporty casual"
            },
            {
                "title": "Summer Wedding",
                "description": "Light-colored suit perfect for daytime celebrations",
                "items": ["Beige Linen Suit", "Pastel Shirt", "Pocket Square", "Suede Loafers"],
                "occasion": "Formal",
                "season": "Spring/Summer",
                "price": "₹19,999",
                "rating": 4.7,
                "image": "💒",
                "shopping_keywords": "men linen suit beige summer wedding"
            }
        ],
        "Inverted Triangle": [
            {
                "title": "V-Neck Balance",
                "description": "V-necklines soften a broad-shouldered frame",
                "items": ["V-Neck Sweater", "Straight-Leg Chinos", "Suede Boots", "Leather Watch"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹9,999",
                "rating": 4.5,
                "image": "🧥",
                "shopping_keywords": "men v neck sweater straight leg chinos casual"
            },
            {
                "title": "Relaxed Fit Office",
                "description": "Softer shoulder blazers with fuller trousers for proportion",
                "items": ["Unstructured Blazer", "Wide-Leg Trousers", "Button-Down Shirt", "Loafers"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹15,999",
                "rating": 4.6,
                "image": "💼",
                "shopping_keywords": "men unstructured blazer wide leg trousers office"
            },
            {
                "title": "Cargo Pants Casual",
                "description": "Cargo pants add volume to the lower body for balance",
                "items": ["Plain Crew-Neck Tee", "Cargo Pants", "Hiking Boots", "Canvas Backpack"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹7,499",
                "rating": 4.4,
                "image": "🎒",
                "shopping_keywords": "men cargo pants crew neck tee casual boots"
            },
            {
                "title": "Dark Shirt Party",
                "description": "Simple dark shirt keeps the focus centered, not on broad shoulders",
                "items": ["Black Mandarin Collar Shirt", "Dark Slim Trousers", "Chelsea Boots", "Silver Chain"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹11,999",
                "rating": 4.6,
                "image": "🎩",
                "shopping_keywords": "men black shirt slim trousers party wear"
            },
            {
                "title": "Slim Formal Suit",
                "description": "Slim-cut suit without excessive shoulder padding",
                "items": ["Slim-Fit Navy Suit", "Light Blue Shirt", "Knit Tie", "Brown Oxfords"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹22,999",
                "rating": 4.8,
                "image": "🤵",
                "shopping_keywords": "men slim fit navy suit formal"
            },
            {
                "title": "Henley Casual Day",
                "description": "Henley neckline draws the eye down from broad shoulders",
                "items": ["Henley T-Shirt", "Relaxed Fit Jeans", "Canvas Sneakers", "Beaded Bracelet"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹5,499",
                "rating": 4.3,
                "image": "👕",
                "shopping_keywords": "men henley tshirt relaxed jeans casual"
            },
            {
                "title": "Bootcut Jean Outfit",
                "description": "Bootcut jeans widen the leg to match broader shoulders",
                "items": ["Plain Polo", "Bootcut Jeans", "Leather Belt", "Suede Desert Boots"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹8,999",
                "rating": 4.4,
                "image": "👖",
                "shopping_keywords": "men bootcut jeans polo shirt desert boots"
            },
            {
                "title": "Layered Casual Winter",
                "description": "Subtle layering that doesn't over-emphasize the shoulders",
                "items": ["Zip-Up Cardigan", "Round-Neck Tee", "Corduroy Pants", "Ankle Boots"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹10,999",
                "rating": 4.5,
                "image": "🧣",
                "shopping_keywords": "men zip cardigan corduroy pants winter casual"
            },
            {
                "title": "Linen Beach",
                "description": "Relaxed linen look that softens a muscular frame",
                "items": ["Linen Camp Shirt", "Linen Shorts", "Leather Sandals", "Aviators"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹6,999",
                "rating": 4.3,
                "image": "🏖️",
                "shopping_keywords": "men linen shirt shorts beach summer"
            },
            {
                "title": "Kurta Pajama Set",
                "description": "Traditional Indian wear with a relaxed shoulder line",
                "items": ["Cotton Kurta", "Pajama Pants", "Kolhapuri Chappals", "Stole"],
                "occasion": "Formal",
                "season": "Spring/Summer",
                "price": "₹9,999",
                "rating": 4.5,
                "image": "🪔",
                "shopping_keywords": "men cotton kurta pajama set indian traditional"
            },
            {
                "title": "Raglan Sleeve Casual",
                "description": "Raglan sleeves visually reduce shoulder width",
                "items": ["Raglan Sleeve Sweatshirt", "Slim Joggers", "Retro Sneakers", "Cap"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹5,999",
                "rating": 4.2,
                "image": "🎽",
                "shopping_keywords": "men raglan sweatshirt slim joggers sneakers"
            },
            {
                "title": "Formal Bandhgala",
                "description": "Indian formal with a clean shoulder line",
                "items": ["Bandhgala Jacket", "Slim Trousers", "Pocket Square", "Brogues"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹17,999",
                "rating": 4.7,
                "image": "🇮🇳",
                "shopping_keywords": "men bandhgala jacket formal indian"
            },
            {
                "title": "Denim Shirt Vibes",
                "description": "Soft denim shirt creates a relaxed upper body look",
                "items": ["Denim Shirt", "Khaki Pants", "White Sneakers", "Leather Watch"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹7,499",
                "rating": 4.4,
                "image": "👔",
                "shopping_keywords": "men denim shirt khaki pants casual outfit"
            },
            {
                "title": "Oversized Tee Street",
                "description": "Oversized top disguises overly broad shoulders for streetwear",
                "items": ["Oversized Graphic Tee", "Wide-Leg Pants", "Platform Sneakers", "Bucket Hat"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹6,499",
                "rating": 4.3,
                "image": "🎒",
                "shopping_keywords": "men oversized graphic tee wide leg pants streetwear"
            },
            {
                "title": "Summer Wedding Guest",
                "description": "Light suit with minimal shoulder detail",
                "items": ["Light Grey Suit", "White Shirt", "Floral Tie", "Tan Oxfords"],
                "occasion": "Formal",
                "season": "Spring/Summer",
                "price": "₹21,999",
                "rating": 4.7,
                "image": "💒",
                "shopping_keywords": "men light grey suit wedding guest summer"
            }
        ],
        "Hourglass": [
            {
                "title": "Fitted Suit Perfection",
                "description": "Tailored suit that follows your natural proportions",
                "items": ["Slim-Fit Suit", "Fitted Shirt", "Silk Tie", "Oxford Shoes"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹24,999",
                "rating": 4.8,
                "image": "🤵",
                "shopping_keywords": "men slim fit tailored suit formal"
            },
            {
                "title": "Fitted Casual",
                "description": "Fitted pieces showcase your balanced proportions",
                "items": ["Fitted V-Neck Tee", "Slim-Fit Jeans", "Clean Sneakers", "Leather Belt"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹6,999",
                "rating": 4.5,
                "image": "👕",
                "shopping_keywords": "men fitted v neck tee slim jeans casual"
            },
            {
                "title": "Smart Layered",
                "description": "Layered blazer look that highlights your waist definition",
                "items": ["Slim Blazer", "Turtleneck", "Tailored Trousers", "Chelsea Boots"],
                "occasion": "Work",
                "season": "Autumn/Winter",
                "price": "₹16,999",
                "rating": 4.7,
                "image": "💼",
                "shopping_keywords": "men slim blazer turtleneck layered outfit"
            },
            {
                "title": "Henley Party",
                "description": "Fitted henley with dark jeans for a smart party look",
                "items": ["Black Henley", "Dark Slim Jeans", "Leather Jacket", "Ankle Boots"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹13,999",
                "rating": 4.6,
                "image": "🎩",
                "shopping_keywords": "men leather jacket henley jeans party outfit"
            },
            {
                "title": "Polo Smart Casual",
                "description": "Well-fitted polo shirt for a put-together casual look",
                "items": ["Slim Polo Shirt", "Chinos", "Boat Shoes", "Aviator Sunglasses"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹7,499",
                "rating": 4.4,
                "image": "🌴",
                "shopping_keywords": "men slim polo shirt chinos boat shoes"
            },
            {
                "title": "Winter Knit Style",
                "description": "Fitted knitwear shows off proportions in colder weather",
                "items": ["Cable-Knit Sweater", "Wool Trousers", "Leather Boots", "Scarf"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹11,999",
                "rating": 4.5,
                "image": "🧣",
                "shopping_keywords": "men cable knit sweater wool trousers winter"
            },
            {
                "title": "Belted Trench Coat",
                "description": "Belted coat that cinches at the waist for a defined look",
                "items": ["Trench Coat", "Fitted Shirt", "Slim Trousers", "Oxford Shoes"],
                "occasion": "Work",
                "season": "Autumn/Winter",
                "price": "₹18,999",
                "rating": 4.7,
                "image": "🧥",
                "shopping_keywords": "men trench coat belted slim fit formal"
            },
            {
                "title": "Workout Flex",
                "description": "Athletic wear that highlights your balanced build",
                "items": ["Compression Tee", "Training Shorts", "Running Shoes", "Fitness Band"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹5,999",
                "rating": 4.3,
                "image": "🏋️",
                "shopping_keywords": "men athletic workout gear compression tee"
            },
            {
                "title": "Ethnic Elegance",
                "description": "Fitted kurta that showcases your proportional build",
                "items": ["Fitted Silk Kurta", "Slim Churidar", "Embroidered Mojari", "Brooch"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹15,999",
                "rating": 4.6,
                "image": "🪔",
                "shopping_keywords": "men fitted silk kurta churidar festive"
            },
            {
                "title": "Monochrome Statement",
                "description": "All-black fitted outfit for maximum impact",
                "items": ["Black Fitted Shirt", "Black Jeans", "Black Chelsea Boots", "Silver Watch"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹12,999",
                "rating": 4.6,
                "image": "🖤",
                "shopping_keywords": "men all black outfit fitted shirt jeans"
            },
            {
                "title": "Summer Fresh",
                "description": "Light, fitted summer outfit for warm weather",
                "items": ["Linen Blend Shirt", "Slim Shorts", "Espadrilles", "Straw Fedora"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹6,499",
                "rating": 4.3,
                "image": "☀️",
                "shopping_keywords": "men linen shirt slim shorts summer"
            },
            {
                "title": "Business Sharp",
                "description": "Slim-cut business separates for daily office wear",
                "items": ["Fitted Blazer", "Slim Dress Shirt", "Tailored Pants", "Monk Straps"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹19,999",
                "rating": 4.7,
                "image": "💼",
                "shopping_keywords": "men fitted blazer dress shirt office business"
            },
            {
                "title": "Retro Weekend",
                "description": "Vintage-inspired fitted pieces for a standout weekend look",
                "items": ["Retro Track Jacket", "Slim Joggers", "Retro Sneakers", "Chain Necklace"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹8,999",
                "rating": 4.4,
                "image": "🎶",
                "shopping_keywords": "men retro track jacket joggers vintage"
            },
            {
                "title": "Formal Black Suit",
                "description": "Classic black suit perfect for any formal occasion",
                "items": ["Black Suit", "White Dress Shirt", "Silver Cufflinks", "Black Oxfords"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹26,999",
                "rating": 4.9,
                "image": "🤵",
                "shopping_keywords": "men black suit formal classic"
            },
            {
                "title": "Denim Day Out",
                "description": "Clean denim look that shows off your proportions",
                "items": ["Fitted Denim Jacket", "White Tee", "Dark Jeans", "Clean Sneakers"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹8,499",
                "rating": 4.4,
                "image": "👖",
                "shopping_keywords": "men denim jacket white tee dark jeans"
            }
        ],
        "Oval": [
            {
                "title": "Vertical Stripe Power",
                "description": "Vertical stripes create a lengthening, slimming effect",
                "items": ["Vertical Stripe Shirt", "Dark Trousers", "Leather Belt", "Oxford Shoes"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹11,999",
                "rating": 4.5,
                "image": "💼",
                "shopping_keywords": "men vertical stripe shirt dark trousers office"
            },
            {
                "title": "Structured Blazer Look",
                "description": "A well-structured blazer creates clean lines over the midsection",
                "items": ["Single-Breasted Blazer", "V-Neck Tee", "Straight-Leg Pants", "Loafers"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹14,999",
                "rating": 4.6,
                "image": "🧥",
                "shopping_keywords": "men structured blazer v neck tee casual"
            },
            {
                "title": "Monochromatic Slim",
                "description": "Single-color outfits create a streamlined vertical line",
                "items": ["Navy Sweater", "Navy Trousers", "Matching Belt", "Brown Derbys"],
                "occasion": "Work",
                "season": "Autumn/Winter",
                "price": "₹13,499",
                "rating": 4.5,
                "image": "👔",
                "shopping_keywords": "men monochromatic navy outfit office"
            },
            {
                "title": "Dark Casual Elegance",
                "description": "Dark tones create a slimming effect for everyday wear",
                "items": ["Black V-Neck Tee", "Dark Wash Jeans", "Black Sneakers", "Minimal Watch"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹6,999",
                "rating": 4.4,
                "image": "🖤",
                "shopping_keywords": "men dark casual outfit v neck jeans"
            },
            {
                "title": "Formal Dark Suit",
                "description": "Dark suit with clean lines for a commanding formal look",
                "items": ["Black Slim Suit", "White Shirt", "Dark Tie", "Patent Shoes"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹24,999",
                "rating": 4.8,
                "image": "🤵",
                "shopping_keywords": "men black slim suit formal dark"
            },
            {
                "title": "Layered Casual Winter",
                "description": "Strategic layering that creates a leaner look in winter",
                "items": ["Long Cardigan", "Plain T-Shirt", "Straight Jeans", "Chelsea Boots"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹10,999",
                "rating": 4.4,
                "image": "🧣",
                "shopping_keywords": "men long cardigan casual winter layered outfit"
            },
            {
                "title": "Untucked Linen",
                "description": "Relaxed untucked linen creates an easy, breezy silhouette",
                "items": ["Loose Linen Shirt", "Linen Shorts", "Sandals", "Sunglasses"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹7,499",
                "rating": 4.3,
                "image": "🌴",
                "shopping_keywords": "men linen shirt shorts beach summer casual"
            },
            {
                "title": "V-Neck Sweater Office",
                "description": "V-neck draws the eye vertically away from the midsection",
                "items": ["V-Neck Sweater", "Dress Shirt", "Slim Trousers", "Monk-Strap Shoes"],
                "occasion": "Work",
                "season": "Autumn/Winter",
                "price": "₹12,999",
                "rating": 4.6,
                "image": "👔",
                "shopping_keywords": "men v neck sweater dress shirt office"
            },
            {
                "title": "Party Dark Shirt",
                "description": "Dark fitted shirt for evening events",
                "items": ["Black Fitted Shirt", "Dark Trousers", "Leather Shoes", "Silver Cufflinks"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹9,999",
                "rating": 4.5,
                "image": "🎩",
                "shopping_keywords": "men black fitted shirt party evening"
            },
            {
                "title": "Kurta Comfort",
                "description": "Flowing kurta drapes well on an oval body shape",
                "items": ["A-Line Kurta", "Straight Pajama", "Kolhapuri Sandals", "Wooden Beads"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹8,499",
                "rating": 4.4,
                "image": "🪔",
                "shopping_keywords": "men a line kurta comfortable indian wear"
            },
            {
                "title": "Overcoat Presence",
                "description": "Long overcoat creates a strong vertical line",
                "items": ["Wool Overcoat", "Fitted Sweater", "Straight Trousers", "Leather Boots"],
                "occasion": "Formal",
                "season": "Autumn/Winter",
                "price": "₹21,999",
                "rating": 4.7,
                "image": "🧥",
                "shopping_keywords": "men wool overcoat winter formal"
            },
            {
                "title": "Jogger Comfort",
                "description": "Tapered joggers with a solid tee for active days",
                "items": ["Performance Tee", "Tapered Joggers", "Running Shoes", "Sports Watch"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹5,999",
                "rating": 4.3,
                "image": "🏃",
                "shopping_keywords": "men tapered joggers performance tee active"
            },
            {
                "title": "Nehru Jacket Formal",
                "description": "Nehru jacket provides structure without cinching at waist",
                "items": ["Nehru Jacket", "Plain Shirt", "Slim Trousers", "Mojari Shoes"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹16,999",
                "rating": 4.6,
                "image": "🇮🇳",
                "shopping_keywords": "men nehru jacket formal indian wear"
            },
            {
                "title": "Polo Day Casual",
                "description": "Structured polo in dark shades for a clean casual look",
                "items": ["Dark Polo Shirt", "Khaki Chinos", "White Sneakers", "Leather Watch"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹6,999",
                "rating": 4.3,
                "image": "👕",
                "shopping_keywords": "men dark polo shirt khaki chinos casual"
            },
            {
                "title": "Wedding Guest Formal",
                "description": "Three-piece dark suit for wedding celebrations",
                "items": ["Three-Piece Dark Suit", "Dress Shirt", "Silk Pocket Square", "Brogues"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹28,999",
                "rating": 4.8,
                "image": "💒",
                "shopping_keywords": "men three piece dark suit wedding formal"
            }
        ]
    }
    return shape_outfits.get(body_shape, shape_outfits["Rectangle"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FEMALE OUTFITS DATABASE (expanded from original 6 → 15 per shape)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _get_female_outfits(body_shape):
    """Return female outfit recommendations by body shape."""
    shape_outfits = {
        "Rectangle": [
            {
                "title": "Defined Waist Elegance",
                "description": "Belted pieces to create curves and define your silhouette",
                "items": ["Belted Trench Coat", "Fitted Midi Dress", "Heeled Ankle Boots", "Statement Belt"],
                "occasion": "Formal",
                "season": "Autumn/Winter",
                "price": "₹18,999",
                "rating": 4.7,
                "image": "👗",
                "shopping_keywords": "women belted trench coat fitted midi dress"
            },
            {
                "title": "Peplum Power",
                "description": "Structured tops that add volume at the waist for a balanced shape",
                "items": ["Peplum Blouse", "Slim Fit Trousers", "Pointed Toe Flats", "Pendant Necklace"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹12,499",
                "rating": 4.5,
                "image": "👚",
                "shopping_keywords": "women peplum blouse slim fit trousers office"
            },
            {
                "title": "A-Line Weekend",
                "description": "Flowy A-line silhouettes for a relaxed yet polished casual look",
                "items": ["A-Line Skirt", "Tucked V-Neck Top", "White Sneakers", "Crossbody Bag"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹8,999",
                "rating": 4.4,
                "image": "👕",
                "shopping_keywords": "women a line skirt v neck top casual"
            },
            {
                "title": "Ruched Party Look",
                "description": "Bodycon with ruching details for a glamorous night out",
                "items": ["Ruched Bodycon Dress", "Strappy Heels", "Clutch Bag", "Drop Earrings"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹14,999",
                "rating": 4.6,
                "image": "✨",
                "shopping_keywords": "women ruched bodycon dress party strappy heels"
            },
            {
                "title": "Layered Office Chic",
                "description": "Structured layers to add dimension and shape to your frame",
                "items": ["Structured Blazer", "High-Waist Pencil Skirt", "Silk Camisole", "Loafers"],
                "occasion": "Work",
                "season": "Autumn/Winter",
                "price": "₹16,499",
                "rating": 4.8,
                "image": "💼",
                "shopping_keywords": "women structured blazer pencil skirt office"
            },
            {
                "title": "Sporty Casual",
                "description": "Athleisure with waist-defining details for active days",
                "items": ["Cropped Hoodie", "High-Waist Joggers", "Chunky Sneakers", "Baseball Cap"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹7,499",
                "rating": 4.3,
                "image": "🏃",
                "shopping_keywords": "women cropped hoodie high waist joggers athleisure"
            },
            {
                "title": "Wrap Dress Day",
                "description": "Wrap dresses create the illusion of curves on a straight frame",
                "items": ["Floral Wrap Dress", "Wedge Sandals", "Straw Tote", "Statement Earrings"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹10,999",
                "rating": 4.5,
                "image": "🌸",
                "shopping_keywords": "women floral wrap dress wedge sandals"
            },
            {
                "title": "Saree Elegance",
                "description": "Draped saree creates beautiful curves on any body shape",
                "items": ["Silk Saree", "Embroidered Blouse", "Gold Jhumkas", "Bangles"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹15,999",
                "rating": 4.7,
                "image": "🥻",
                "shopping_keywords": "women silk saree embroidered blouse festive"
            },
            {
                "title": "Maxi Skirt Boho",
                "description": "Flowing maxi skirt with a tucked top for boho vibes",
                "items": ["Printed Maxi Skirt", "Crop Top", "Gladiator Sandals", "Layered Necklaces"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹8,499",
                "rating": 4.3,
                "image": "🌻",
                "shopping_keywords": "women printed maxi skirt crop top boho"
            },
            {
                "title": "Cocktail Shimmer",
                "description": "Sequined dress with waist detail for evening glamour",
                "items": ["Sequined Mini Dress", "Stiletto Heels", "Crystal Clutch", "Diamond Studs"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹19,999",
                "rating": 4.8,
                "image": "💎",
                "shopping_keywords": "women sequined dress party cocktail shimmer"
            },
            {
                "title": "Denim Chic",
                "description": "Structured denim jacket adds shape to a straight silhouette",
                "items": ["Cropped Denim Jacket", "Sundress", "Ankle Boots", "Canvas Tote"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹9,499",
                "rating": 4.4,
                "image": "👖",
                "shopping_keywords": "women cropped denim jacket sundress casual"
            },
            {
                "title": "Kurti Casual",
                "description": "Embellished kurti with waist detailing for everyday charm",
                "items": ["Anarkali Kurti", "Churidar Leggings", "Juttis", "Oxidized Earrings"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹6,999",
                "rating": 4.4,
                "image": "🇮🇳",
                "shopping_keywords": "women anarkali kurti churidar casual indian"
            },
            {
                "title": "Power Suit",
                "description": "Tailored women's suit for boardroom confidence",
                "items": ["Fitted Pantsuit", "Silk Blouse", "Pointed Pumps", "Structured Bag"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹22,999",
                "rating": 4.8,
                "image": "💼",
                "shopping_keywords": "women fitted pantsuit silk blouse office"
            },
            {
                "title": "Lehenga Festive",
                "description": "Festive lehenga with structured blouse for celebrations",
                "items": ["Embroidered Lehenga", "Fitted Choli", "Dupatta", "Maang Tikka"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹25,999",
                "rating": 4.9,
                "image": "🪔",
                "shopping_keywords": "women embroidered lehenga festive wedding"
            },
            {
                "title": "Cozy Knit Winter",
                "description": "Belted knit dress for warmth with a defined waist",
                "items": ["Belted Sweater Dress", "Knee-High Boots", "Wool Scarf", "Leather Gloves"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹13,999",
                "rating": 4.5,
                "image": "🧣",
                "shopping_keywords": "women belted sweater dress knee high boots winter"
            }
        ],
        "Triangle": [
            {
                "title": "Structured Shoulder Statement",
                "description": "Broad-shoulder tops to balance wider hips beautifully",
                "items": ["Structured Shoulder Blazer", "Dark Bootcut Jeans", "Pointed Heels", "Tote Bag"],
                "occasion": "Work",
                "season": "Autumn/Winter",
                "price": "₹15,999",
                "rating": 4.7,
                "image": "💼",
                "shopping_keywords": "women structured blazer bootcut jeans office"
            },
            {
                "title": "V-Neck Balance",
                "description": "V-necklines draw the eye upward for balanced proportion",
                "items": ["V-Neck Wrap Top", "A-Line Midi Skirt", "Wedge Sandals", "Pendant Necklace"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹9,999",
                "rating": 4.5,
                "image": "👚",
                "shopping_keywords": "women v neck wrap top a line midi skirt"
            },
            {
                "title": "Bold Top Party Look",
                "description": "Embellished tops that draw attention upward for evening glamour",
                "items": ["Sequined Off-Shoulder Top", "Dark Slim Pants", "Statement Earrings", "Stiletto Heels"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹13,499",
                "rating": 4.6,
                "image": "✨",
                "shopping_keywords": "women sequined off shoulder top party wear"
            },
            {
                "title": "Boat Neck Formal",
                "description": "Wide necklines to enhance shoulder line for formal events",
                "items": ["Boat Neck Dress", "Tailored Dark Trousers", "Kitten Heels", "Clutch Purse"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹17,999",
                "rating": 4.8,
                "image": "👗",
                "shopping_keywords": "women boat neck dress formal kitten heels"
            },
            {
                "title": "Casual Confidence",
                "description": "Relaxed fit tops with darker bottoms for easy everyday style",
                "items": ["Graphic Tee", "Dark Wash A-Line Jeans", "Canvas Sneakers", "Denim Jacket"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹6,999",
                "rating": 4.3,
                "image": "👕",
                "shopping_keywords": "women graphic tee dark jeans denim jacket casual"
            },
            {
                "title": "Ruffled Elegance",
                "description": "Ruffled details on top add volume and balance proportions",
                "items": ["Ruffle Blouse", "Straight Leg Trousers", "Block Heels", "Stud Earrings"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹11,499",
                "rating": 4.5,
                "image": "👚",
                "shopping_keywords": "women ruffle blouse straight leg trousers"
            },
            {
                "title": "Off-Shoulder Boho",
                "description": "Off-shoulder tops widen the upper body for a balanced look",
                "items": ["Off-Shoulder Maxi Dress", "Flat Sandals", "Boho Earrings", "Woven Bag"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹10,499",
                "rating": 4.4,
                "image": "🌸",
                "shopping_keywords": "women off shoulder maxi dress boho casual"
            },
            {
                "title": "Puffer Jacket Winter",
                "description": "Padded jacket adds upper body volume in cold weather",
                "items": ["Cropped Puffer Jacket", "Dark Leggings", "Ankle Boots", "Beanie"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹9,999",
                "rating": 4.4,
                "image": "❄️",
                "shopping_keywords": "women cropped puffer jacket leggings winter"
            },
            {
                "title": "Salwar Kameez Grace",
                "description": "Embellished dupatta draws attention to the upper body",
                "items": ["Printed Salwar Kameez", "Embroidered Dupatta", "Juttis", "Bangles"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹8,999",
                "rating": 4.5,
                "image": "🇮🇳",
                "shopping_keywords": "women salwar kameez embroidered dupatta"
            },
            {
                "title": "Cape Sleeve Elegance",
                "description": "Cape sleeves add dramatic width to the shoulders",
                "items": ["Cape Sleeve Dress", "Stiletto Heels", "Pearl Clutch", "Diamond Pendant"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹16,999",
                "rating": 4.7,
                "image": "👗",
                "shopping_keywords": "women cape sleeve dress formal elegant"
            },
            {
                "title": "Jogger Athleisure",
                "description": "Sporty look with a boxy crop top to balance proportions",
                "items": ["Boxy Crop Top", "High-Waist Joggers", "Running Shoes", "Sports Watch"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹5,999",
                "rating": 4.2,
                "image": "🏃",
                "shopping_keywords": "women boxy crop top joggers athleisure"
            },
            {
                "title": "Blazer Power Look",
                "description": "Double-breasted blazer creates a commanding upper body",
                "items": ["Double-Breasted Blazer", "Slim Pants", "Pumps", "Structured Bag"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹18,999",
                "rating": 4.7,
                "image": "💼",
                "shopping_keywords": "women double breasted blazer slim pants office"
            },
            {
                "title": "Palazzo Party",
                "description": "Flowing palazzo pants with an embellished top",
                "items": ["Embellished Crop Top", "Palazzo Pants", "Statement Earrings", "Strappy Heels"],
                "occasion": "Party",
                "season": "Spring/Summer",
                "price": "₹12,499",
                "rating": 4.5,
                "image": "✨",
                "shopping_keywords": "women palazzo pants crop top party outfit"
            },
            {
                "title": "Lehenga Glow",
                "description": "Voluminous lehenga with fitted choli for festive beauty",
                "items": ["Flared Lehenga", "Fitted Choli", "Heavy Dupatta", "Jhumka Earrings"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹24,999",
                "rating": 4.9,
                "image": "🪔",
                "shopping_keywords": "women lehenga fitted choli festive wedding"
            },
            {
                "title": "Midi Dress Brunch",
                "description": "Fit-and-flare midi for weekend brunches",
                "items": ["Fit-and-Flare Midi", "Kitten Heels", "Crossbody Bag", "Sun Hat"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹9,999",
                "rating": 4.4,
                "image": "🌷",
                "shopping_keywords": "women fit and flare midi dress brunch outfit"
            }
        ],
        "Inverted Triangle": [
            {
                "title": "Wide-Leg Balance",
                "description": "Voluminous bottoms to balance broad shoulders gracefully",
                "items": ["Simple V-Neck Tee", "Wide-Leg Palazzo Pants", "Platform Sandals", "Hoop Earrings"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹8,499",
                "rating": 4.5,
                "image": "👕",
                "shopping_keywords": "women v neck tee palazzo pants casual"
            },
            {
                "title": "A-Line Skirt Harmony",
                "description": "Flared skirts that add fullness below the waist",
                "items": ["Wrap Top", "Flared A-Line Skirt", "Ankle Strap Heels", "Bracelet Set"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹12,999",
                "rating": 4.6,
                "image": "👗",
                "shopping_keywords": "women wrap top flared a line skirt office"
            },
            {
                "title": "Boyfriend Jeans Relaxed",
                "description": "Relaxed boyfriend jeans to balance the broader upper body",
                "items": ["Slim Fit Shirt", "Boyfriend Jeans", "Loafers", "Leather Belt"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹10,999",
                "rating": 4.4,
                "image": "👖",
                "shopping_keywords": "women boyfriend jeans relaxed casual outfit"
            },
            {
                "title": "Peplum Evening",
                "description": "Peplum details at the hip for a balanced party silhouette",
                "items": ["Peplum Cocktail Dress", "Stiletto Pumps", "Statement Clutch", "Chandelier Earrings"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹16,499",
                "rating": 4.7,
                "image": "✨",
                "shopping_keywords": "women peplum cocktail dress party"
            },
            {
                "title": "Tailored Professional",
                "description": "Soft shoulder blazers with full skirts for office elegance",
                "items": ["Soft Blazer", "Full Circle Skirt", "Pointed Flats", "Structured Handbag"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹14,999",
                "rating": 4.8,
                "image": "💼",
                "shopping_keywords": "women soft blazer circle skirt office professional"
            },
            {
                "title": "Flowing Formal",
                "description": "Draped fabrics that soften broad shoulders for formal events",
                "items": ["Draped Maxi Dress", "Delicate Sandals", "Pearl Necklace", "Satin Clutch"],
                "occasion": "Formal",
                "season": "Spring/Summer",
                "price": "₹19,999",
                "rating": 4.9,
                "image": "👗",
                "shopping_keywords": "women draped maxi dress formal elegant"
            },
            {
                "title": "Flared Skirt Casual",
                "description": "Flared midi skirt adds volume below to balance broad shoulders",
                "items": ["Fitted Crop Top", "Flared Midi Skirt", "Flat Sandals", "Straw Bag"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹7,999",
                "rating": 4.3,
                "image": "🌸",
                "shopping_keywords": "women flared midi skirt crop top casual"
            },
            {
                "title": "Anarkali Grace",
                "description": "Flowing anarkali adds fullness below for Indian elegance",
                "items": ["Anarkali Suit", "Churidar", "Mojari", "Maang Tikka"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹14,999",
                "rating": 4.7,
                "image": "🥻",
                "shopping_keywords": "women anarkali suit indian festive"
            },
            {
                "title": "High-Waist Wide Jeans",
                "description": "Wide-leg jeans add proportion to a V-shaped frame",
                "items": ["Simple Blouse", "High-Waist Wide-Leg Jeans", "Platform Sneakers", "Tote Bag"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹8,999",
                "rating": 4.4,
                "image": "👖",
                "shopping_keywords": "women high waist wide leg jeans casual"
            },
            {
                "title": "Sarong Beach Look",
                "description": "Flowy sarong adds lower-body volume for beach or resort",
                "items": ["Halter Top", "Printed Sarong", "Flat Sandals", "Shell Necklace"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹5,999",
                "rating": 4.2,
                "image": "🏖️",
                "shopping_keywords": "women halter top sarong beach outfit"
            },
            {
                "title": "Lehenga Full Flare",
                "description": "Maximum lower-body volume for weddings and celebrations",
                "items": ["Full Flare Lehenga", "Slim Choli", "Organza Dupatta", "Jhumkas"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹28,999",
                "rating": 4.9,
                "image": "🪔",
                "shopping_keywords": "women full flare lehenga wedding festive"
            },
            {
                "title": "Jogger Athleisure",
                "description": "Sleek top with cargo joggers for sporty days",
                "items": ["Racerback Tank", "Cargo Joggers", "Running Shoes", "Sports Watch"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹6,499",
                "rating": 4.3,
                "image": "🏃",
                "shopping_keywords": "women racerback cargo joggers athleisure"
            },
            {
                "title": "Tulip Skirt Office",
                "description": "Tulip skirt adds hip fullness for work elegance",
                "items": ["V-Neck Blouse", "Tulip Skirt", "Pumps", "Pearl Earrings"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹13,499",
                "rating": 4.6,
                "image": "💼",
                "shopping_keywords": "women tulip skirt v neck blouse office"
            },
            {
                "title": "Jumpsuit Party",
                "description": "Wide-leg jumpsuit with a halter neck for party nights",
                "items": ["Wide-Leg Jumpsuit", "Stiletto Heels", "Chain Belt", "Cuff Bracelet"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹14,999",
                "rating": 4.6,
                "image": "✨",
                "shopping_keywords": "women wide leg jumpsuit party night"
            },
            {
                "title": "Winter Knit Layers",
                "description": "Soft knit layers that don't add bulk to shoulders",
                "items": ["Soft Cardigan", "Bootcut Jeans", "Ankle Boots", "Wool Scarf"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹10,999",
                "rating": 4.4,
                "image": "🧣",
                "shopping_keywords": "women soft cardigan bootcut jeans winter"
            }
        ],
        "Hourglass": [
            {
                "title": "Wrapped Perfection",
                "description": "Wrap dresses that hug your curves and define the waist",
                "items": ["Wrap Midi Dress", "Nude Pumps", "Gold Pendant", "Envelope Clutch"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹15,999",
                "rating": 4.8,
                "image": "👗",
                "shopping_keywords": "women wrap midi dress formal elegant"
            },
            {
                "title": "Fitted Office Look",
                "description": "Tailored pieces that follow your natural curves professionally",
                "items": ["Fitted Blazer", "High-Waist Pencil Skirt", "Silk Blouse", "Classic Pumps"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹18,499",
                "rating": 4.7,
                "image": "💼",
                "shopping_keywords": "women fitted blazer pencil skirt office"
            },
            {
                "title": "High-Waist Casual",
                "description": "High-waisted pieces with fitted tops for effortless style",
                "items": ["V-Neck Fitted Tee", "High-Waist Flare Jeans", "Ballet Flats", "Tote Bag"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹9,499",
                "rating": 4.5,
                "image": "👕",
                "shopping_keywords": "women high waist flare jeans fitted tee casual"
            },
            {
                "title": "Bodycon Glam",
                "description": "Figure-hugging dress to showcase your hourglass curves",
                "items": ["Bodycon Cocktail Dress", "Strappy Heels", "Crystal Earrings", "Minaudière Bag"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹14,999",
                "rating": 4.9,
                "image": "✨",
                "shopping_keywords": "women bodycon cocktail dress party"
            },
            {
                "title": "Belted Trench Classic",
                "description": "Timeless belted trench that cinches at the waist beautifully",
                "items": ["Belted Trench Coat", "Fitted Turtleneck", "Slim Trousers", "Knee-High Boots"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹17,499",
                "rating": 4.6,
                "image": "🧥",
                "shopping_keywords": "women belted trench coat turtleneck winter"
            },
            {
                "title": "Corset Detail Evening",
                "description": "Structured corset details for a dramatic evening silhouette",
                "items": ["Corset Top", "High-Waist Wide Pants", "Platform Heels", "Statement Necklace"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹13,999",
                "rating": 4.7,
                "image": "👚",
                "shopping_keywords": "women corset top high waist pants party"
            },
            {
                "title": "Saree Queen",
                "description": "Draped saree that beautifully accentuates hourglass curves",
                "items": ["Chiffon Saree", "Fitted Short Blouse", "Gold Earrings", "Bangles"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹12,999",
                "rating": 4.8,
                "image": "🥻",
                "shopping_keywords": "women chiffon saree fitted blouse festive"
            },
            {
                "title": "Fit-and-Flare Romance",
                "description": "Classic fit-and-flare dress for feminine charm",
                "items": ["Fit-and-Flare Dress", "Kitten Heels", "Pearl Studs", "Crossbody Bag"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹10,499",
                "rating": 4.5,
                "image": "🌸",
                "shopping_keywords": "women fit and flare dress casual kitten heels"
            },
            {
                "title": "Jumpsuit Chic",
                "description": "Belted jumpsuit that defines the waist for a polished look",
                "items": ["Belted Jumpsuit", "Block Heels", "Statement Earrings", "Structured Clutch"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹14,999",
                "rating": 4.6,
                "image": "💼",
                "shopping_keywords": "women belted jumpsuit block heels work"
            },
            {
                "title": "Lehenga Goddess",
                "description": "Fitted lehenga that follows your natural curves",
                "items": ["Mermaid Lehenga", "Fitted Blouse", "Net Dupatta", "Kundan Jewelry"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹32,999",
                "rating": 4.9,
                "image": "🪔",
                "shopping_keywords": "women mermaid lehenga fitted blouse wedding"
            },
            {
                "title": "Midi Skirt Smart",
                "description": "High-waist midi skirt for a smart casual day out",
                "items": ["Crop Turtleneck", "High-Waist Midi Skirt", "Ankle Boots", "Leather Bag"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹11,999",
                "rating": 4.5,
                "image": "🧥",
                "shopping_keywords": "women high waist midi skirt crop turtleneck"
            },
            {
                "title": "Summer Sundress",
                "description": "Cinched-waist sundress for warm-weather perfection",
                "items": ["Cinched Sundress", "Flat Sandals", "Straw Hat", "Canvas Tote"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹7,999",
                "rating": 4.4,
                "image": "☀️",
                "shopping_keywords": "women cinched waist sundress summer"
            },
            {
                "title": "Cocktail Slit Dress",
                "description": "Thigh-slit dress for a bold cocktail party entrance",
                "items": ["Slit Maxi Dress", "Stiletto Heels", "Rhinestone Clutch", "Cuff Bracelet"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹18,999",
                "rating": 4.7,
                "image": "✨",
                "shopping_keywords": "women slit maxi dress cocktail party"
            },
            {
                "title": "Anarkali Elegance",
                "description": "Fitted bodice anarkali flows beautifully from the waist",
                "items": ["Fitted Anarkali", "Churidar", "Dupatta", "Jhumka Earrings"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹13,999",
                "rating": 4.6,
                "image": "🇮🇳",
                "shopping_keywords": "women fitted anarkali churidar festive"
            },
            {
                "title": "Denim Day Date",
                "description": "Fitted denim look that celebrates your curves",
                "items": ["Denim Jacket", "Fitted Dress", "White Sneakers", "Layered Necklaces"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹9,999",
                "rating": 4.4,
                "image": "👖",
                "shopping_keywords": "women denim jacket fitted dress casual date"
            }
        ],
        "Oval": [
            {
                "title": "Empire Waist Grace",
                "description": "Empire waist dresses that flow elegantly from under the bust",
                "items": ["Empire Waist Maxi Dress", "Wedge Sandals", "Long Necklace", "Oversized Sunglasses"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹11,999",
                "rating": 4.6,
                "image": "👗",
                "shopping_keywords": "women empire waist maxi dress casual"
            },
            {
                "title": "Monochromatic Power",
                "description": "Single color head-to-toe for a sleek, elongating effect",
                "items": ["Long Cardigan", "Matching Trousers", "V-Neck Camisole", "Loafers"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹14,499",
                "rating": 4.5,
                "image": "💼",
                "shopping_keywords": "women monochromatic outfit long cardigan office"
            },
            {
                "title": "Draped Elegance",
                "description": "Draped fabrics that skim the body for a flattering formal look",
                "items": ["Draped Sheath Dress", "Kitten Heels", "Pearl Studs", "Silk Scarf"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹16,999",
                "rating": 4.7,
                "image": "👗",
                "shopping_keywords": "women draped sheath dress formal"
            },
            {
                "title": "V-Neck Casual",
                "description": "Elongating V-neck tops paired with wide-leg comfort",
                "items": ["V-Neck Tunic", "Wide-Leg Linen Pants", "Flat Sandals", "Beaded Bracelet"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹7,999",
                "rating": 4.4,
                "image": "👕",
                "shopping_keywords": "women v neck tunic wide leg linen pants"
            },
            {
                "title": "Asymmetric Party",
                "description": "Asymmetric hemlines and draping for a chic party look",
                "items": ["Asymmetric Hem Dress", "Ankle Strap Heels", "Statement Ring", "Metallic Clutch"],
                "occasion": "Party",
                "season": "All Season",
                "price": "₹13,499",
                "rating": 4.6,
                "image": "✨",
                "shopping_keywords": "women asymmetric hem dress party"
            },
            {
                "title": "Structured Jacket Look",
                "description": "A structured jacket creates clean lines over a flowing base",
                "items": ["Structured Jacket", "Straight-Leg Pants", "Oxford Shoes", "Minimalist Watch"],
                "occasion": "Work",
                "season": "Autumn/Winter",
                "price": "₹15,499",
                "rating": 4.5,
                "image": "🧥",
                "shopping_keywords": "women structured jacket straight leg pants office"
            },
            {
                "title": "A-Line Tunic",
                "description": "Flowy A-line tunic skims beautifully over the midsection",
                "items": ["A-Line Tunic Top", "Slim Leggings", "Ankle Boots", "Crossbody Bag"],
                "occasion": "Casual",
                "season": "Autumn/Winter",
                "price": "₹8,999",
                "rating": 4.4,
                "image": "👚",
                "shopping_keywords": "women a line tunic leggings casual"
            },
            {
                "title": "Kaftan Elegance",
                "description": "Flowing kaftan for effortless elegance on any occasion",
                "items": ["Embroidered Kaftan", "Slim Pants", "Gold Sandals", "Statement Earrings"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹9,999",
                "rating": 4.5,
                "image": "🌺",
                "shopping_keywords": "women embroidered kaftan casual elegant"
            },
            {
                "title": "Saree Drape",
                "description": "Pre-stitched saree drapes beautifully for a slimming effect",
                "items": ["Pre-Stitched Saree", "Fitted Blouse", "Gold Jewelry Set", "Bindi"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹14,999",
                "rating": 4.7,
                "image": "🥻",
                "shopping_keywords": "women pre stitched saree fitted blouse festive"
            },
            {
                "title": "Dark Blazer Office",
                "description": "Dark-toned blazer for a sleek, streamlined office presence",
                "items": ["Black Blazer", "White Blouse", "Dark Trousers", "Pointed Pumps"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹16,999",
                "rating": 4.6,
                "image": "💼",
                "shopping_keywords": "women black blazer white blouse office formal"
            },
            {
                "title": "Palazzo Breeze",
                "description": "Flowing palazzo pants with a fitted top for summer comfort",
                "items": ["Fitted Tank Top", "Printed Palazzo Pants", "Strappy Sandals", "Straw Bag"],
                "occasion": "Casual",
                "season": "Spring/Summer",
                "price": "₹7,499",
                "rating": 4.3,
                "image": "🌴",
                "shopping_keywords": "women palazzo pants tank top casual summer"
            },
            {
                "title": "Layered Cocktail",
                "description": "Layered cocktail outfit with vertical details for lengthening",
                "items": ["Waterfall Cardigan", "Bodycon Dress", "Stiletto Heels", "Jeweled Clutch"],
                "occasion": "Party",
                "season": "Autumn/Winter",
                "price": "₹15,999",
                "rating": 4.6,
                "image": "✨",
                "shopping_keywords": "women waterfall cardigan bodycon dress party"
            },
            {
                "title": "Churidar Comfort",
                "description": "Straight-cut kurti with churidar for everyday Indian wear",
                "items": ["Straight-Cut Kurti", "Churidar", "Mojari", "Oxidized Earrings"],
                "occasion": "Casual",
                "season": "All Season",
                "price": "₹6,499",
                "rating": 4.3,
                "image": "🇮🇳",
                "shopping_keywords": "women straight cut kurti churidar casual"
            },
            {
                "title": "Shift Dress Simple",
                "description": "Shift dress in a solid dark color for a clean, easy silhouette",
                "items": ["Dark Shift Dress", "Pointed Flats", "Long Pendant", "Tote Bag"],
                "occasion": "Work",
                "season": "All Season",
                "price": "₹10,999",
                "rating": 4.4,
                "image": "👗",
                "shopping_keywords": "women dark shift dress office simple"
            },
            {
                "title": "Wedding Guest Drape",
                "description": "Draped gown for wedding celebrations with a flattering silhouette",
                "items": ["Draped Floor-Length Gown", "Embellished Sandals", "Diamond Earrings", "Satin Clutch"],
                "occasion": "Formal",
                "season": "All Season",
                "price": "₹22,999",
                "rating": 4.8,
                "image": "💒",
                "shopping_keywords": "women draped gown wedding guest formal"
            }
        ]
    }
    return shape_outfits.get(body_shape, shape_outfits["Rectangle"])
