import { Palette, User, Sparkles, TrendingUp, ArrowRight, Shield, Ruler, Eye, UserCheck } from 'lucide-react';
import { useEffect, useState } from 'react';

interface AnalysisResultProps {
  onNavigate: (page: string) => void;
  analysisData?: any;
  recommendationsData?: any;
  userPhotoUrl?: string | null;
}

function CircularProgress({ value, size = 120, strokeWidth = 8 }: { value: number; size?: number; strokeWidth?: number }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;
  
  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size/2} cy={size/2} r={radius} stroke="#fce7f3" strokeWidth={strokeWidth} fill="none" />
        <circle
          cx={size/2} cy={size/2} r={radius}
          stroke="url(#progressGradient)"
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="circular-progress"
          style={{
            '--circumference': circumference,
            '--dash-offset': offset,
            transition: 'stroke-dashoffset 1.5s ease-out'
          } as any}
        />
        <defs>
          <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#e11d48" />
            <stop offset="100%" stopColor="#ec4899" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-gray-900">{value}%</span>
        <span className="text-xs text-gray-500 font-medium">Confidence</span>
      </div>
    </div>
  );
}

const bodyShapeIcons: Record<string, string> = {
  'Rectangle': '▬',
  'Triangle': '▽',
  'Inverted Triangle': '△',
  'Hourglass': '⧖',
  'Oval': '⬭',
};

const bodyShapeDescriptions: Record<string, string> = {
  'Rectangle': 'Your shoulders, waist, and hips are similar in width, creating a balanced, athletic silhouette.',
  'Triangle': 'Your hips are wider than your shoulders, creating a beautiful pear-shaped silhouette.',
  'Inverted Triangle': 'Your shoulders are broader than your hips, creating a strong, athletic upper body.',
  'Hourglass': 'Your bust and hips are balanced with a defined waistline, creating classic curves.',
  'Oval': 'Your midsection is the widest part of your body, with a rounded, full silhouette.',
};

const skinToneSwatches: Record<string, { bg: string; text: string; label: string }> = {
  'Light': { bg: '#FAEBD7', text: '#8B6914', label: 'Light / Fair' },
  'Medium': { bg: '#D2A679', text: '#5C3317', label: 'Medium / Warm' },
  'Dark': { bg: '#8B6914', text: '#FFFFFF', label: 'Dark / Deep' },
};

export default function AnalysisResult({ onNavigate, analysisData, recommendationsData, userPhotoUrl }: AnalysisResultProps) {
  const [animateIn, setAnimateIn] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setAnimateIn(true), 100);
    return () => clearTimeout(t);
  }, []);

  // If no analysis data, redirect to upload
  if (!analysisData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-rose-50 via-pink-50 to-orange-50 flex items-center justify-center py-12 px-4">
        <div className="text-center max-w-md">
          <div className="bg-rose-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
            <Eye className="w-10 h-10 text-rose-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-3">No Analysis Found</h2>
          <p className="text-gray-600 mb-8">Upload a photo first to get your personalized style analysis.</p>
          <button
            onClick={() => onNavigate('upload')}
            className="bg-gradient-to-r from-rose-500 to-pink-500 text-white px-8 py-3 rounded-full font-medium hover:shadow-xl hover:shadow-rose-200 transition-all hover:scale-105"
          >
            Upload Photo
          </button>
        </div>
      </div>
    );
  }

  const bodyType = analysisData.body_shape || analysisData.bodyType || 'Rectangle';
  const skinTone = analysisData.skin_tone || analysisData.skinTone || 'Medium';
  const detectedGender = analysisData.detected_gender || recommendationsData?.gender || '';
  const confidenceScore = analysisData.confidence_score 
    ? Math.round(parseFloat(analysisData.confidence_score) * (parseFloat(analysisData.confidence_score) <= 1 ? 100 : 1)) 
    : 85;
  const measurements = analysisData.body_measurements || analysisData.measurements || {};

  // Get color palette - from recommendations or analysis
  const colorPalette = recommendationsData?.color_palette 
    || analysisData.color_palette 
    || [];

  // Get style tips from recommendations
  const styleTips = recommendationsData?.styles || [];
  const summary = recommendationsData?.summary || '';

  const skinSwatch = skinToneSwatches[skinTone] || skinToneSwatches['Medium'];
  const genderLabel = detectedGender === 'Male' ? "Men's Fashion" : "Women's Fashion";
  const genderDesc = detectedGender === 'Male'
    ? 'Outfits curated for masculine builds and proportions'
    : 'Outfits curated for feminine silhouettes and style';

  const profileCards = [
    {
      icon: <User className="w-5 h-5" />,
      label: 'Body Shape',
      value: bodyType,
      desc: bodyShapeDescriptions[bodyType] || 'Your unique body shape',
      gradient: 'from-rose-500 to-pink-500',
    },
    {
      icon: <Palette className="w-5 h-5" />,
      label: 'Skin Tone',
      value: skinSwatch.label,
      desc: `Best suited for ${skinTone === 'Light' ? 'jewel tones and deep colors' : skinTone === 'Dark' ? 'bright and pastel colors' : 'earthy warm colors'}`,
      gradient: 'from-orange-500 to-rose-500',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-pink-50 to-orange-50 py-8 md:py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8 md:mb-10">
          <div className="inline-flex items-center space-x-2 bg-green-50 text-green-700 px-4 py-2 rounded-full mb-4 border border-green-200">
            <Sparkles className="w-4 h-4" />
            <span className="text-sm font-semibold">Analysis Complete</span>
          </div>
          <h1 className="text-3xl md:text-5xl font-bold text-gray-900 mb-3" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Your Style Profile
          </h1>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Here's what our AI discovered about your unique fashion aesthetic
          </p>
        </div>

        {/* Top section: Photo + Confidence + Profile Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
          {/* User Photo */}
          {userPhotoUrl && (
            <div className="lg:col-span-3 animate-fade-in-up">
              <div className="bg-white rounded-2xl p-3 shadow-lg overflow-hidden">
                <div className="relative rounded-xl overflow-hidden aspect-[3/4]">
                  <img
                    src={userPhotoUrl}
                    alt="Your uploaded photo"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
                </div>
                <p className="text-xs text-gray-500 text-center mt-2 font-medium">Your Photo</p>
              </div>
            </div>
          )}

          {/* Profile Cards + Confidence */}
          <div className={`${userPhotoUrl ? 'lg:col-span-9' : 'lg:col-span-12'}`}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 stagger-children">
              {/* Body Shape Card */}
              <div className="bg-white rounded-2xl p-6 shadow-lg card-hover">
                <div className={`bg-gradient-to-br ${profileCards[0].gradient} w-11 h-11 rounded-xl flex items-center justify-center text-white mb-4`}>
                  {profileCards[0].icon}
                </div>
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">{profileCards[0].label}</h3>
                <p className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-2">
                  <span className="text-3xl">{bodyShapeIcons[bodyType] || '●'}</span>
                  {profileCards[0].value}
                </p>
                <p className="text-sm text-gray-500 leading-relaxed">{profileCards[0].desc}</p>
              </div>

              {/* Skin Tone Card */}
              <div className="bg-white rounded-2xl p-6 shadow-lg card-hover">
                <div className={`bg-gradient-to-br ${profileCards[1].gradient} w-11 h-11 rounded-xl flex items-center justify-center text-white mb-4`}>
                  {profileCards[1].icon}
                </div>
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">{profileCards[1].label}</h3>
                <div className="flex items-center gap-3 mb-2">
                  <div 
                    className="w-10 h-10 rounded-lg shadow-inner border-2 border-white"
                    style={{ backgroundColor: skinSwatch.bg, boxShadow: `0 2px 8px ${skinSwatch.bg}66` }}
                  />
                  <p className="text-2xl font-bold text-gray-900">{skinTone}</p>
                </div>
                <p className="text-sm text-gray-500 leading-relaxed">{profileCards[1].desc}</p>
              </div>

              {/* Gender Detection Card */}
              {detectedGender && (
                <div className="bg-white rounded-2xl p-6 shadow-lg card-hover">
                  <div className="bg-gradient-to-br from-violet-500 to-purple-500 w-11 h-11 rounded-xl flex items-center justify-center text-white mb-4">
                    <UserCheck className="w-5 h-5" />
                  </div>
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Detected Gender</h3>
                  <p className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-2">
                    <span className="text-3xl">{detectedGender === 'Male' ? '👨' : '👩'}</span>
                    {genderLabel}
                  </p>
                  <p className="text-sm text-gray-500 leading-relaxed">{genderDesc}</p>
                </div>
              )}

              {/* Confidence Score */}
              <div className="bg-white rounded-2xl p-6 shadow-lg card-hover flex flex-col items-center justify-center text-center">
                <CircularProgress value={confidenceScore} />
                <div className="mt-3">
                  <div className="flex items-center justify-center gap-1.5 mb-1">
                    <Shield className="w-4 h-4 text-green-500" />
                    <span className="text-xs font-semibold text-green-600 uppercase tracking-wider">AI Accuracy</span>
                  </div>
                  <p className="text-sm text-gray-500">Based on {confidenceScore > 90 ? 'excellent' : confidenceScore > 75 ? 'good' : 'moderate'} image quality</p>
                </div>
              </div>
            </div>

            {/* Body Measurements (if available) */}
            {measurements.shoulder_hip_ratio && (
              <div className="mt-6 bg-white rounded-2xl p-6 shadow-lg animate-fade-in-up" style={{ animationDelay: '300ms' }}>
                <div className="flex items-center space-x-2 mb-4">
                  <Ruler className="w-5 h-5 text-rose-500" />
                  <h3 className="font-semibold text-gray-900">Body Proportions</h3>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {measurements.shoulder_width_norm && (
                    <div className="bg-rose-50 rounded-xl p-3 text-center">
                      <p className="text-xs text-gray-500 mb-1">Shoulder Width</p>
                      <p className="text-lg font-bold text-gray-900">{(measurements.shoulder_width_norm * 100).toFixed(1)}</p>
                    </div>
                  )}
                  {measurements.hip_width_norm && (
                    <div className="bg-pink-50 rounded-xl p-3 text-center">
                      <p className="text-xs text-gray-500 mb-1">Hip Width</p>
                      <p className="text-lg font-bold text-gray-900">{(measurements.hip_width_norm * 100).toFixed(1)}</p>
                    </div>
                  )}
                  {measurements.waist_width_est && (
                    <div className="bg-orange-50 rounded-xl p-3 text-center">
                      <p className="text-xs text-gray-500 mb-1">Waist (Est.)</p>
                      <p className="text-lg font-bold text-gray-900">{(measurements.waist_width_est * 100).toFixed(1)}</p>
                    </div>
                  )}
                  {measurements.shoulder_hip_ratio && (
                    <div className="bg-purple-50 rounded-xl p-3 text-center">
                      <p className="text-xs text-gray-500 mb-1">S/H Ratio</p>
                      <p className="text-lg font-bold text-gray-900">{parseFloat(measurements.shoulder_hip_ratio).toFixed(2)}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Color Palette + Style Tips */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Color Palette */}
          <div className="bg-white rounded-2xl p-6 md:p-8 shadow-lg animate-fade-in-up" style={{ animationDelay: '200ms' }}>
            <div className="flex items-center space-x-3 mb-6">
              <div className="bg-gradient-to-br from-rose-500 to-pink-500 w-10 h-10 rounded-xl flex items-center justify-center">
                <Palette className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Your Color Palette</h2>
                <p className="text-sm text-gray-500">Colors that complement your {skinTone.toLowerCase()} skin tone</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 stagger-children">
              {colorPalette.length > 0 ? colorPalette.map((color: any, index: number) => (
                <div
                  key={index}
                  className="flex items-center space-x-3 p-3 rounded-xl border border-gray-100 hover:border-rose-200 hover:shadow-md transition-all group"
                >
                  <div
                    className="w-12 h-12 rounded-lg shadow-sm flex-shrink-0 border-2 border-white group-hover:scale-110 transition-transform"
                    style={{ backgroundColor: color.hex, boxShadow: `0 4px 12px ${color.hex}44` }}
                  />
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-gray-900 text-sm">{color.name}</h4>
                    <p className="text-xs text-gray-500 truncate">{color.description}</p>
                    <span className="text-xs text-gray-400 font-mono">{color.hex}</span>
                  </div>
                </div>
              )) : (
                /* Fallback palette if none from backend */
                [
                  { name: 'Recommended 1', hex: '#e11d48', description: 'Primary accent' },
                  { name: 'Recommended 2', hex: '#ec4899', description: 'Soft complement' },
                ].map((color, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 rounded-xl border border-gray-100">
                    <div className="w-12 h-12 rounded-lg shadow-sm" style={{ backgroundColor: color.hex }} />
                    <div>
                      <h4 className="font-semibold text-gray-900 text-sm">{color.name}</h4>
                      <p className="text-xs text-gray-500">{color.description}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Style Tips */}
          <div className="bg-white rounded-2xl p-6 md:p-8 shadow-lg animate-fade-in-up" style={{ animationDelay: '300ms' }}>
            <div className="flex items-center space-x-3 mb-6">
              <div className="bg-gradient-to-br from-orange-500 to-rose-500 w-10 h-10 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Style Recommendations</h2>
                <p className="text-sm text-gray-500">Clothing styles for your {bodyType} body shape</p>
              </div>
            </div>

            {styleTips.length > 0 ? (
              <ul className="space-y-3 stagger-children">
                {styleTips.map((tip: string, index: number) => (
                  <li key={index} className="flex items-start space-x-3 p-3 rounded-xl bg-gradient-to-r from-rose-50/80 to-pink-50/40 border border-rose-100/50 hover:shadow-sm transition-all">
                    <div className="bg-white w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm border border-rose-100">
                      <span className="text-xs font-bold text-rose-500">{index + 1}</span>
                    </div>
                    <p className="text-gray-700 text-sm leading-relaxed">{tip}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-center py-8 text-gray-400">
                <p>Style tips will appear after ML analysis completes.</p>
              </div>
            )}

            {summary && (
              <div className="mt-6 p-4 bg-gradient-to-r from-rose-50 to-orange-50 rounded-xl border border-rose-100">
                <p className="text-sm text-gray-700 italic leading-relaxed">"{summary}"</p>
              </div>
            )}
          </div>
        </div>

        {/* CTA Banner */}
        <div className="bg-gradient-to-r from-rose-500 via-pink-500 to-rose-600 rounded-2xl p-8 md:p-12 text-center text-white shadow-xl animate-fade-in-up relative overflow-hidden" style={{ animationDelay: '400ms' }}>
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-4 left-8 w-20 h-20 rounded-full bg-white" />
            <div className="absolute bottom-4 right-12 w-32 h-32 rounded-full bg-white" />
          </div>
          <div className="relative z-10">
            <h2 className="text-2xl md:text-3xl font-bold mb-3" style={{ fontFamily: 'Outfit, sans-serif' }}>Ready to See Your Curated Outfits?</h2>
            <p className="text-lg mb-8 opacity-90 max-w-xl mx-auto">
              We've hand-picked {detectedGender === 'Male' ? "men's" : "women's"} outfit combinations based on your {bodyType} body shape and {skinTone.toLowerCase()} skin tone
            </p>
            <button
              onClick={() => onNavigate('recommendations')}
              className="bg-white text-rose-600 px-8 py-4 rounded-full font-semibold text-lg hover:shadow-2xl transition-all hover:scale-105 inline-flex items-center space-x-2 group"
            >
              <span>View Outfit Recommendations</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
