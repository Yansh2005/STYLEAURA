"""
Outfit Image Search – Uses SerpAPI Google Shopping to fetch real product images.
Falls back to curated Unsplash images when SerpAPI key is not configured.
"""
import os
import time
import logging
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

outfit_images_bp = Blueprint('outfit_images', __name__)

# ── In-memory cache (TTL = 24 hours) ──────────────────────────────────────────
_image_cache = {}
_CACHE_TTL = 86400  # 24 hours in seconds


def _cache_get(key):
    entry = _image_cache.get(key)
    if entry and (time.time() - entry['ts']) < _CACHE_TTL:
        return entry['data']
    return None


def _cache_set(key, data):
    _image_cache[key] = {'data': data, 'ts': time.time()}


# ── Price formatter ──────────────────────────────────────────────────────────────────

def _format_price(price_val):
    """Normalize price to a clean string like '₹1,299' (no floats)."""
    if price_val is None or price_val == '':
        return ''
    try:
        num = float(str(price_val).replace(',', '').replace('₹', '').strip())
        return f'₹{int(num):,}'
    except (ValueError, TypeError):
        return str(price_val)


# ── SerpAPI search ────────────────────────────────────────────────────────────

def _search_serpapi(query, num_results=6):
    """Search Google Shopping via SerpAPI and return product image results."""
    api_key = os.environ.get('SERPAPI_KEY', '')
    if not api_key or api_key == 'PASTE_YOUR_SERPAPI_KEY_HERE':
        return None

    try:
        from serpapi import GoogleSearch
        params = {
            'engine': 'google_shopping',
            'q': query,
            'api_key': api_key,
            'num': num_results,
            'hl': 'en',
            'gl': 'in'      # India — change if needed
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        shopping_results = results.get('shopping_results', [])
        images = []
        for item in shopping_results[:num_results]:
            images.append({
                'url': item.get('thumbnail', ''),
                'title': item.get('title', ''),
                'price': _format_price(item.get('extracted_price', item.get('price', ''))),
                'link': item.get('link', ''),
                'source': item.get('source', ''),
                'rating': item.get('rating'),
                'reviews': item.get('reviews'),
            })
        return images if images else None
    except ImportError:
        logger.warning("serpapi package not installed. Run: pip install google-search-results")
        return None
    except Exception as e:
        logger.error(f"SerpAPI search failed: {e}")
        return None


# ── Curated Unsplash fallback ─────────────────────────────────────────────────

_UNSPLASH_FALLBACKS = {
    # ── Male outfits ──────────────────────────────────────────────────────────────────
    'men suit': [
        {'url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=500&fit=crop', 'title': 'Classic Suit', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400&h=500&fit=crop', 'title': 'Formal Suit Look', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men casual': [
        {'url': 'https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?w=400&h=500&fit=crop', 'title': 'Casual Menswear', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1490578474895-699cd4e2cf59?w=400&h=500&fit=crop', 'title': 'Everyday Style', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men party': [
        {'url': 'https://images.unsplash.com/photo-1617137968427-85924c800a22?w=400&h=500&fit=crop', 'title': 'Party Wear', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=400&h=500&fit=crop', 'title': 'Night Out Look', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men blazer': [
        {'url': 'https://images.unsplash.com/photo-1555069519-127aadedf1ee?w=400&h=500&fit=crop', 'title': 'Smart Blazer', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1516914943479-89db7d9ae7f2?w=400&h=500&fit=crop', 'title': 'Business Casual', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men formal': [
        {'url': 'https://images.unsplash.com/photo-1598808503746-f34c53b9323e?w=400&h=500&fit=crop', 'title': 'Formal Menswear', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1542050735-9574564073f4?w=400&h=500&fit=crop', 'title': 'Office Formal', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men jacket': [
        {'url': 'https://images.unsplash.com/photo-1543076447-215ad9ba6923?w=400&h=500&fit=crop', 'title': 'Jacket Style', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1578932750294-f5075e85f44a?w=400&h=500&fit=crop', 'title': 'Casual Jacket', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men jeans': [
        {'url': 'https://images.unsplash.com/photo-1548126032-079a0fb0099d?w=400&h=500&fit=crop', 'title': 'Denim Casual', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400&h=500&fit=crop', 'title': 'Jeans Look', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men kurta': [
        {'url': 'https://images.unsplash.com/photo-1609205807107-ae53b166d3b9?w=400&h=500&fit=crop', 'title': 'Traditional Kurta', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1610652492500-ded49ceeb378?w=400&h=500&fit=crop', 'title': 'Festive Wear', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men athleisure': [
        {'url': 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=400&h=500&fit=crop', 'title': 'Athleisure Style', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1571945192086-a8edd4e36c27?w=400&h=500&fit=crop', 'title': 'Sports Casual', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men streetwear': [
        {'url': 'https://images.unsplash.com/photo-1523398002811-999ca8dec234?w=400&h=500&fit=crop', 'title': 'Street Style', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1556906781-9a412961d28b?w=400&h=500&fit=crop', 'title': 'Urban Look', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men linen': [
        {'url': 'https://images.unsplash.com/photo-1604644401890-0bd678c83788?w=400&h=500&fit=crop', 'title': 'Linen Summer', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1596755389378-c31d21fd1273?w=400&h=500&fit=crop', 'title': 'Beach Style', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men tuxedo': [
        {'url': 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400&h=500&fit=crop', 'title': 'Tuxedo Look', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1605518216938-7c31b7b14ad0?w=400&h=500&fit=crop', 'title': 'Black Tie', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men polo': [
        {'url': 'https://images.unsplash.com/photo-1501370753897-22e7aa35e5f6?w=400&h=500&fit=crop', 'title': 'Polo Casual', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men winter': [
        {'url': 'https://images.unsplash.com/photo-1545291730-faff8ca1d4b0?w=400&h=500&fit=crop', 'title': 'Winter Look', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1548864698-34c4b3ab3b62?w=400&h=500&fit=crop', 'title': 'Warm Winter Style', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'men wedding': [
        {'url': 'https://images.unsplash.com/photo-1537268942164-0684270c3008?w=400&h=500&fit=crop', 'title': 'Wedding Guest', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1609902726285-00668009f004?w=400&h=500&fit=crop', 'title': 'Celebration Wear', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    # ── Female outfits ───────────────────────────────────────────────────────────────
    'women dress': [
        {'url': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400&h=500&fit=crop', 'title': 'Elegant Dress', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=400&h=500&fit=crop', 'title': 'Formal Dress', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women casual': [
        {'url': 'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=400&h=500&fit=crop', 'title': 'Casual Fashion', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1485968579580-b6d095142e6e?w=400&h=500&fit=crop', 'title': 'Everyday Style', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women party': [
        {'url': 'https://images.unsplash.com/photo-1518577915332-c2a19f149a75?w=400&h=500&fit=crop', 'title': 'Party Outfit', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=400&h=500&fit=crop', 'title': 'Night Out Look', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women formal': [
        {'url': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&h=500&fit=crop', 'title': 'Power Dressing', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=400&h=500&fit=crop', 'title': 'Office Formal', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women blouse': [
        {'url': 'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&h=500&fit=crop', 'title': 'Blouse Style', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400&h=500&fit=crop', 'title': 'Smart Casual Top', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women skirt': [
        {'url': 'https://images.unsplash.com/photo-1583496661160-fb5218ees06a?w=400&h=500&fit=crop', 'title': 'Skirt Look', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=500&fit=crop', 'title': 'A-Line Style', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women kurta': [
        {'url': 'https://images.unsplash.com/photo-1610189019599-e2d0b48d7a63?w=400&h=500&fit=crop', 'title': 'Festive Kurta', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1606791405792-1004f1718d0c?w=400&h=500&fit=crop', 'title': 'Traditional Wear', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women saree': [
        {'url': 'https://images.unsplash.com/photo-1610452220379-c38e51fb5bea?w=400&h=500&fit=crop', 'title': 'Saree Elegance', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1583391733956-6c78276477e2?w=400&h=500&fit=crop', 'title': 'Festive Saree', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women wrap': [
        {'url': 'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=400&h=500&fit=crop', 'title': 'Wrap Dress', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1548549557-dbe9946621da?w=400&h=500&fit=crop', 'title': 'Elegant Wrap', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women summer': [
        {'url': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=500&fit=crop', 'title': 'Summer Style', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1555212697-194d092e3b8f?w=400&h=500&fit=crop', 'title': 'Beach Fashion', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women winter': [
        {'url': 'https://images.unsplash.com/photo-1548123378-bd1d3c9dfde1?w=400&h=500&fit=crop', 'title': 'Winter Chic', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1516762689617-e1cffcef479d?w=400&h=500&fit=crop', 'title': 'Cozy Winter Look', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women jacket': [
        {'url': 'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=400&h=500&fit=crop', 'title': 'Jacket Style', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1564584217132-2271feaeb3c5?w=400&h=500&fit=crop', 'title': 'Casual Jacket', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women peplum': [
        {'url': 'https://images.unsplash.com/photo-1502716119720-b23a93e5fe1b?w=400&h=500&fit=crop', 'title': 'Peplum Style', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women monochromatic': [
        {'url': 'https://images.unsplash.com/photo-1594938291221-94f18cbb5e30?w=400&h=500&fit=crop', 'title': 'Monochrome Look', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
    'women wedding': [
        {'url': 'https://images.unsplash.com/photo-1566177978-5a9e59dfb44e?w=400&h=500&fit=crop', 'title': 'Wedding Guest', 'price': '', 'link': '', 'source': 'Unsplash'},
        {'url': 'https://images.unsplash.com/photo-1537670443948-5e7f1c887e3f?w=400&h=500&fit=crop', 'title': 'Celebration Wear', 'price': '', 'link': '', 'source': 'Unsplash'},
    ],
}


def _get_fallback_images(query):
    """Return curated fallback images based on keyword matching."""
    query_lower = query.lower()
    best_match = None
    best_score = 0

    for key, images in _UNSPLASH_FALLBACKS.items():
        # Count matching keywords
        score = sum(1 for word in key.split() if word in query_lower)
        if score > best_score:
            best_score = score
            best_match = images

    return best_match or []


# ── API Endpoint ──────────────────────────────────────────────────────────────

@outfit_images_bp.route('/outfit-images', methods=['GET'])
def search_outfit_images():
    """
    Search for outfit product images.
    Query params:
      - q: Search query (required), e.g. "men navy blue suit blazer formal"
      - n: Number of results (optional, default 6, max 10)
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Missing required query parameter "q"'}), 400

    num_results = min(int(request.args.get('n', 6)), 10)

    # Check cache first
    cache_key = f"{query}:{num_results}"
    cached = _cache_get(cache_key)
    if cached:
        return jsonify({'images': cached, 'source': 'cache'}), 200

    # Try SerpAPI
    images = _search_serpapi(query, num_results)
    if images:
        _cache_set(cache_key, images)
        return jsonify({'images': images, 'source': 'google_shopping'}), 200

    # Fallback to curated images
    fallback = _get_fallback_images(query)
    return jsonify({'images': fallback, 'source': 'fallback'}), 200
