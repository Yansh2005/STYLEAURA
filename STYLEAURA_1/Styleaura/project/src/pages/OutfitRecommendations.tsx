import { Heart, ShoppingBag, Sparkles, Filter, Star, ExternalLink, Palette, User as UserIcon, ChevronDown, Loader2, ImageIcon } from 'lucide-react';
import { useState, useMemo, useEffect, useCallback } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface OutfitRecommendationsProps {
  onNavigate: (page: string) => void;
  onNewUpload?: () => void;
  analysisData?: any;
  recommendationsData?: any;
  userPhotoUrl?: string | null;
}

const OCCASIONS = ['All', 'Casual', 'Work', 'Formal', 'Party'];
const SEASONS = ['All Season', 'Spring/Summer', 'Autumn/Winter'];
const ITEMS_PER_PAGE = 8;

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Format a price value (number or string) to ₹X,XXX */
function formatPrice(price: string | number): string {
  const num = typeof price === 'number' ? price : parseFloat(String(price).replace(/[^\d.]/g, ''));
  if (isNaN(num)) return String(price);
  return `₹${Math.round(num).toLocaleString('en-IN')}`;
}

/** Clean raw API product titles — strip size/variant suffixes */
function cleanTitle(title: string): string {
  return title
    .replace(/\s*[-–|]\s*(Size|Sizes?|M|L|XL|XXL|S)[^)]*$/i, '')
    .replace(/\s*\([^)]{0,30}\)\s*$/g, '')
    .trim();
}

// ── Product Image Component ──────────────────────────────────────────────────
function ProductImage({ query, className = '' }: { query: string; className?: string }) {
  const [images, setImages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    if (!query) return;
    let cancelled = false;

    const fetchImages = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(`${API_URL}/api/ml/outfit-images?q=${encodeURIComponent(query)}&n=3`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (!cancelled && res.ok) {
          const data = await res.json();
          setImages(data.images || []);
        }
      } catch {
        // Silently fail — will show fallback
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchImages();
    return () => { cancelled = true; };
  }, [query]);

  if (loading) {
    return (
      <div className={`flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-50 ${className}`}>
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="w-6 h-6 text-rose-400 animate-spin" />
          <span className="text-xs text-gray-400">Loading products...</span>
        </div>
      </div>
    );
  }

  if (images.length === 0 || hasError) {
    return (
      <div className={`flex items-center justify-center bg-gradient-to-br from-rose-50 via-pink-50 to-orange-50 ${className}`}>
        <div className="flex flex-col items-center gap-2 text-gray-400">
          <ImageIcon className="w-8 h-8" />
          <span className="text-xs font-medium">Product preview</span>
        </div>
      </div>
    );
  }

  const img = images[currentIdx];
  return (
    <div className={`relative group overflow-hidden ${className}`}>
      <img
        src={img.url}
        alt={img.title || 'Product'}
        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
        onError={() => setHasError(true)}
      />
      {/* Image navigation dots */}
      {images.length > 1 && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5">
          {images.map((_: any, i: number) => (
            <button
              key={i}
              onClick={(e) => { e.stopPropagation(); setCurrentIdx(i); }}
              className={`w-2 h-2 rounded-full transition-all ${i === currentIdx ? 'bg-white scale-125 shadow-md' : 'bg-white/50 hover:bg-white/80'}`}
            />
          ))}
        </div>
      )}
      {/* Product info overlay */}
      {(img.title || img.price != null || img.source) && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3 translate-y-full group-hover:translate-y-0 transition-transform duration-300">
          {img.title && (
            <p className="text-white text-xs font-semibold leading-tight line-clamp-2 mb-1">
              {cleanTitle(img.title)}
            </p>
          )}
          <div className="flex items-center justify-between">
            {img.price != null && img.price !== '' && (
              <p className="text-white/90 text-xs font-bold">{formatPrice(img.price)}</p>
            )}
            {img.source && img.source !== 'Unsplash' && (
              <span className="text-[10px] text-white/80 bg-white/20 px-1.5 py-0.5 rounded-full">
                {img.source}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


export default function OutfitRecommendations({ onNavigate, onNewUpload, analysisData, recommendationsData, userPhotoUrl }: OutfitRecommendationsProps) {
  const [favorites, setFavorites] = useState<number[]>(() => {
    try {
      const saved = localStorage.getItem('styleaura_favorites');
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });
  const [selectedOccasion, setSelectedOccasion] = useState('All');
  const [selectedSeason, setSelectedSeason] = useState('All Season');
  const [visibleCount, setVisibleCount] = useState(ITEMS_PER_PAGE);

  const bodyShape = analysisData?.body_shape || analysisData?.bodyType || '';
  const skinTone = analysisData?.skin_tone || analysisData?.skinTone || '';
  const detectedGender = analysisData?.detected_gender || recommendationsData?.gender || '';

  // Use real recommendation data if available
  const outfits = recommendationsData?.outfits || [];
  const colorPalette = recommendationsData?.color_palette || [];
  const stylesList = recommendationsData?.styles || [];
  const colorsList = recommendationsData?.colors || [];

  // Filter outfits
  const filteredOutfits = useMemo(() => {
    return outfits.filter((outfit: any) => {
      const matchOccasion = selectedOccasion === 'All' || outfit.occasion === selectedOccasion;
      const matchSeason = selectedSeason === 'All Season' || outfit.season === selectedSeason || outfit.season === 'All Season';
      return matchOccasion && matchSeason;
    });
  }, [outfits, selectedOccasion, selectedSeason]);

  // Reset visible count when filters change
  useEffect(() => {
    setVisibleCount(ITEMS_PER_PAGE);
  }, [selectedOccasion, selectedSeason]);

  const visibleOutfits = filteredOutfits.slice(0, visibleCount);
  const hasMore = visibleCount < filteredOutfits.length;

  const toggleFavorite = (index: number) => {
    setFavorites((prev) => {
      const next = prev.includes(index) ? prev.filter((f) => f !== index) : [...prev, index];
      localStorage.setItem('styleaura_favorites', JSON.stringify(next));
      return next;
    });
  };

  const handleShop = (outfit: any) => {
    const keywords = outfit.shopping_keywords || outfit.items?.join(' ') || outfit.title;
    const genderPrefix = detectedGender === 'Male' ? 'mens' : 'womens';
    const searchUrl = `https://www.google.com/search?tbm=shop&q=${encodeURIComponent(genderPrefix + ' ' + keywords)}`;
    window.open(searchUrl, '_blank');
  };

  const handleLoadMore = () => {
    setVisibleCount(prev => prev + ITEMS_PER_PAGE);
  };

  // If no recommendations data at all, show a fallback
  if (!recommendationsData || outfits.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-rose-50 via-pink-50 to-orange-50 py-12 px-4">
        <div className="max-w-2xl mx-auto text-center">
          <div className="bg-rose-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
            <ShoppingBag className="w-10 h-10 text-rose-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-3">No Outfit Recommendations Yet</h2>
          <p className="text-gray-600 mb-8">
            Upload a photo and complete your style analysis to get personalized outfit recommendations.
          </p>
          <button
            onClick={() => onNavigate('upload')}
            className="bg-gradient-to-r from-rose-500 to-pink-500 text-white px-8 py-3 rounded-full font-medium hover:shadow-xl hover:shadow-rose-200 transition-all hover:scale-105"
          >
            Get Started
          </button>
        </div>
      </div>
    );
  }

  const genderLabel = detectedGender === 'Male' ? "Men's" : "Women's";

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-pink-50 to-orange-50 py-8 md:py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center space-x-2 bg-rose-100 text-rose-600 px-4 py-2 rounded-full mb-4 border border-rose-200">
            <Sparkles className="w-4 h-4" />
            <span className="text-sm font-semibold">Personalized for You</span>
          </div>
          <h1 className="text-3xl md:text-5xl font-bold text-gray-900 mb-3" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Your Curated {genderLabel} Outfits
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            {filteredOutfits.length} {genderLabel.toLowerCase()} outfit combinations tailored to your {bodyShape} body shape & {skinTone.toLowerCase()} skin tone
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar — Style Profile Summary */}
          <div className="lg:col-span-1 space-y-6">
            {/* Style Profile Card */}
            <div className="bg-white rounded-2xl p-6 shadow-lg sticky top-24">
              <h3 className="font-bold text-gray-900 text-sm uppercase tracking-wider mb-4 flex items-center gap-2">
                <UserIcon className="w-4 h-4 text-rose-500" />
                Your Style Profile
              </h3>

              {userPhotoUrl && (
                <div className="mb-4 rounded-xl overflow-hidden aspect-[3/4]">
                  <img src={userPhotoUrl} alt="You" className="w-full h-full object-cover object-top" />
                </div>
              )}

              <div className="space-y-3 mb-6">
                {detectedGender && (
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-xs text-gray-500 font-medium">Gender</span>
                    <span className="text-sm font-semibold text-gray-900 flex items-center gap-1">
                      <span>{detectedGender === 'Male' ? '👨' : '👩'}</span>
                      {detectedGender}
                    </span>
                  </div>
                )}
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-xs text-gray-500 font-medium">Body Shape</span>
                  <span className="text-sm font-semibold text-gray-900">{bodyShape}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-xs text-gray-500 font-medium">Skin Tone</span>
                  <span className="text-sm font-semibold text-gray-900">{skinTone}</span>
                </div>
              </div>

              {/* Top Colors */}
              {colorPalette.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                    <Palette className="w-3.5 h-3.5" />
                    Your Colors
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {colorPalette.slice(0, 6).map((c: any, i: number) => (
                      <div key={i} className="group relative">
                        <div
                          className="w-9 h-9 rounded-lg shadow-sm border-2 border-white cursor-pointer hover:scale-110 transition-transform"
                          style={{ backgroundColor: c.hex, boxShadow: `0 2px 8px ${c.hex}44` }}
                          title={c.name}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Styles */}
              {stylesList.length > 0 && (
                <div className="mt-5 pt-5 border-t border-gray-100">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Best Styles</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {stylesList.map((style: string, i: number) => (
                      <span key={i} className="text-xs bg-rose-50 text-rose-600 px-2.5 py-1 rounded-full font-medium border border-rose-100">
                        {style}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={() => onNavigate('analysis')}
                className="mt-5 w-full text-sm text-rose-600 hover:text-rose-700 font-medium py-2 rounded-xl hover:bg-rose-50 transition-all"
              >
                ← Back to Analysis
              </button>
            </div>
          </div>

          {/* Main Content — Outfit Cards */}
          <div className="lg:col-span-3">
            {/* Filters */}
            <div className="bg-white rounded-2xl p-4 shadow-sm mb-6 flex flex-col sm:flex-row gap-4 items-start sm:items-center">
              <div className="flex items-center gap-2 text-gray-500">
                <Filter className="w-4 h-4" />
                <span className="text-sm font-medium">Filter:</span>
              </div>
              
              {/* Occasion Filter */}
              <div className="flex flex-wrap gap-1.5">
                {OCCASIONS.map(occ => (
                  <button
                    key={occ}
                    onClick={() => setSelectedOccasion(occ)}
                    className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
                      selectedOccasion === occ
                        ? 'bg-rose-500 text-white shadow-md shadow-rose-200'
                        : 'bg-gray-100 text-gray-600 hover:bg-rose-50 hover:text-rose-600'
                    }`}
                  >
                    {occ}
                  </button>
                ))}
              </div>

              <div className="hidden sm:block w-px h-6 bg-gray-200" />

              {/* Season Filter */}
              <div className="flex flex-wrap gap-1.5">
                {SEASONS.map(season => (
                  <button
                    key={season}
                    onClick={() => setSelectedSeason(season)}
                    className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
                      selectedSeason === season
                        ? 'bg-orange-500 text-white shadow-md shadow-orange-200'
                        : 'bg-gray-100 text-gray-600 hover:bg-orange-50 hover:text-orange-600'
                    }`}
                  >
                    {season}
                  </button>
                ))}
              </div>
            </div>

            {/* Results Count */}
            <p className="text-sm text-gray-500 mb-4 font-medium">
              Showing {visibleOutfits.length} of {filteredOutfits.length} {genderLabel.toLowerCase()} outfits
            </p>

            {/* Outfit Grid */}
            {visibleOutfits.length > 0 ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 stagger-children">
                  {visibleOutfits.map((outfit: any, index: number) => (
                    <div
                      key={index}
                      className="bg-white rounded-2xl overflow-hidden shadow-lg card-hover group flex flex-col"
                    >
                      {/* Product Image */}
                      <ProductImage
                        query={outfit.shopping_keywords || outfit.title}
                        className="h-48 w-full"
                      />

                      {/* Card Header — Occasion/Season + Gender + Favorite */}
                      <div className="relative p-5 flex flex-col flex-1">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex gap-2 flex-wrap">
                            {/* Gender Badge */}
                            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full shadow-sm ${
                              detectedGender === 'Male'
                                ? 'text-blue-600 bg-blue-50 border border-blue-100'
                                : 'text-pink-600 bg-pink-50 border border-pink-100'
                            }`}>
                              {detectedGender === 'Male' ? '👨 Men' : '👩 Women'}
                            </span>
                            <span className="text-xs font-semibold text-rose-600 bg-rose-50 px-2.5 py-1 rounded-full shadow-sm border border-rose-100">
                              {outfit.occasion}
                            </span>
                            <span className="text-xs font-medium text-orange-600 bg-orange-50 px-2.5 py-1 rounded-full shadow-sm border border-orange-100">
                              {outfit.season}
                            </span>
                          </div>
                          <button
                            onClick={() => toggleFavorite(index)}
                            className="bg-white w-9 h-9 rounded-full flex items-center justify-center shadow-md hover:scale-110 transition-all flex-shrink-0"
                          >
                            <Heart className={`w-4 h-4 ${favorites.includes(index) ? 'fill-rose-500 text-rose-500' : 'text-gray-400'}`} />
                          </button>
                        </div>

                        {/* Title */}
                        <div className="flex items-center gap-3 mb-3">
                          <span className="text-3xl">{outfit.image || '👗'}</span>
                          <div>
                            <h3 className="text-lg font-bold text-gray-900">{outfit.title}</h3>
                            <p className="text-xs text-gray-500">{outfit.description}</p>
                          </div>
                        </div>

                        {/* Why this suits you */}
                        <div className="flex flex-wrap gap-1.5 mb-3">
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-100 px-2.5 py-1 rounded-full">
                            <span>✓</span> {bodyShape} shape match
                          </span>
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-violet-700 bg-violet-50 border border-violet-100 px-2.5 py-1 rounded-full">
                            <span>✓</span> {outfit.occasion} ready
                          </span>
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-100 px-2.5 py-1 rounded-full">
                            <span>✓</span> {skinTone} tone colors
                          </span>
                        </div>

                        {/* Items */}
                        <div className="space-y-2 mb-4">
                          {outfit.items?.map((item: string, i: number) => (
                            <div key={i} className="flex items-center space-x-2 text-sm text-gray-700">
                              <div className="w-1.5 h-1.5 bg-rose-400 rounded-full flex-shrink-0" />
                              <span>{item}</span>
                            </div>
                          ))}
                        </div>

                        {/* Rating only — real product price shows on image overlay */}
                        <div className="flex items-center justify-end mb-4 pb-4 border-b border-gray-100">
                          {outfit.rating && (
                            <div className="flex items-center gap-1.5">
                              <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                              <span className="text-sm font-semibold text-gray-700">{outfit.rating}</span>
                              <span className="text-xs text-gray-400">/ 5</span>
                            </div>
                          )}
                        </div>

                        {/* Shop Button */}
                        <button style={{ marginTop: 'auto' }}
                          onClick={() => handleShop(outfit)}
                          className="w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center space-x-2 transition-all bg-gradient-to-r from-rose-500 to-pink-500 text-white hover:shadow-lg hover:shadow-rose-200 hover:scale-[1.02] active:scale-[0.98]"
                        >
                          <ShoppingBag className="w-4 h-4" />
                          <span>Shop on Google</span>
                          <ExternalLink className="w-3.5 h-3.5 opacity-60" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Load More Button */}
                {hasMore && (
                  <div className="mt-8 text-center">
                    <button
                      onClick={handleLoadMore}
                      className="inline-flex items-center gap-2 bg-white text-gray-700 px-8 py-3 rounded-full font-semibold shadow-lg hover:shadow-xl border border-gray-200 hover:border-rose-300 transition-all hover:scale-105 active:scale-95"
                    >
                      <ChevronDown className="w-5 h-5" />
                      Load More Outfits ({filteredOutfits.length - visibleCount} remaining)
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-16 bg-white rounded-2xl shadow-lg">
                <Filter className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No outfits match your filters</h3>
                <p className="text-gray-500 mb-4">Try adjusting your occasion or season filter</p>
                <button
                  onClick={() => { setSelectedOccasion('All'); setSelectedSeason('All Season'); }}
                  className="text-rose-600 font-medium hover:underline"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-12 text-center">
          <div className="bg-white rounded-2xl p-8 shadow-lg inline-block max-w-lg animate-fade-in-up" style={{ animationDelay: '500ms' }}>
            <p className="text-gray-600 mb-4 font-medium">Want fresh recommendations?</p>
            <button
              onClick={() => onNewUpload ? onNewUpload() : onNavigate('upload')}
              className="bg-gradient-to-r from-rose-500 to-pink-500 text-white px-8 py-3 rounded-full font-medium hover:shadow-xl hover:shadow-rose-200 transition-all hover:scale-105"
            >
              Upload New Photo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
