import { Camera, BarChart3, Heart, Settings, Clock, Sparkles, ArrowRight, Image as ImageIcon, User as UserIcon } from 'lucide-react';
import { useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface DashboardProps {
  onNavigate: (page: string) => void;
  onAnalysisSelect?: (analysis: any) => void;
  user?: any;
}

export default function Dashboard({ onNavigate, onAnalysisSelect, user }: DashboardProps) {
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [images, setImages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) { setLoading(false); return; }

    try {
      const [analysesRes, imagesRes] = await Promise.all([
        fetch(`${API_URL}/api/analysis/?page=1&per_page=5`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }).catch(() => null),
        fetch(`${API_URL}/api/images/?page=1&per_page=6`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }).catch(() => null),
      ]);

      if (analysesRes?.ok) {
        const data = await analysesRes.json();
        setAnalyses(data.analyses || []);
      }
      if (imagesRes?.ok) {
        const data = await imagesRes.json();
        setImages(data.images || []);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTimeAgo = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  const favoriteCount = (() => {
    try {
      const saved = localStorage.getItem('styleaura_favorites');
      return saved ? JSON.parse(saved).length : 0;
    } catch { return 0; }
  })();

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-pink-50 to-orange-50 py-8 md:py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Welcome Header */}
        <div className="mb-8 animate-fade-in-up">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Welcome back{user?.first_name ? `, ${user.first_name}` : ''}! ✨
          </h1>
          <p className="text-gray-600">Here's your style journey so far</p>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 stagger-children">
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 card-hover">
            <div className="bg-rose-100 w-10 h-10 rounded-xl flex items-center justify-center mb-3">
              <BarChart3 className="w-5 h-5 text-rose-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{analyses.length}</p>
            <p className="text-xs text-gray-500 font-medium">Analyses</p>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 card-hover">
            <div className="bg-blue-100 w-10 h-10 rounded-xl flex items-center justify-center mb-3">
              <ImageIcon className="w-5 h-5 text-blue-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{images.length}</p>
            <p className="text-xs text-gray-500 font-medium">Photos</p>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 card-hover">
            <div className="bg-pink-100 w-10 h-10 rounded-xl flex items-center justify-center mb-3">
              <Heart className="w-5 h-5 text-pink-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{favoriteCount}</p>
            <p className="text-xs text-gray-500 font-medium">Favorites</p>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 card-hover">
            <div className="bg-green-100 w-10 h-10 rounded-xl flex items-center justify-center mb-3">
              <Sparkles className="w-5 h-5 text-green-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {analyses.length > 0 ? `${Math.round(parseFloat(analyses[0]?.confidence_score || '0') * 100) || '—'}%` : '—'}
            </p>
            <p className="text-xs text-gray-500 font-medium">Latest Score</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column — Profile + Quick Actions */}
          <div className="space-y-6">
            {/* Profile Card */}
            <div className="bg-white rounded-2xl p-6 shadow-lg animate-fade-in-up">
              <div className="flex items-center gap-4 mb-5">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-rose-400 to-pink-500 flex items-center justify-center shadow-lg shadow-rose-200">
                  <span className="text-2xl font-bold text-white">
                    {(user?.first_name || user?.email)?.[0]?.toUpperCase() || 'U'}
                  </span>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">
                    {user?.first_name} {user?.last_name}
                  </h3>
                  <p className="text-sm text-gray-500">{user?.email}</p>
                  {user?.created_at && (
                    <p className="text-xs text-gray-400 mt-0.5">
                      Member since {new Date(user.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-2xl p-6 shadow-lg animate-fade-in-up" style={{ animationDelay: '100ms' }}>
              <h3 className="font-bold text-gray-900 text-sm uppercase tracking-wider mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <button
                  onClick={() => onNavigate('upload')}
                  className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-rose-50 transition-all text-left group"
                >
                  <div className="bg-rose-100 w-10 h-10 rounded-xl flex items-center justify-center group-hover:bg-rose-200 transition-colors">
                    <Camera className="w-5 h-5 text-rose-500" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-gray-900">New Analysis</p>
                    <p className="text-xs text-gray-500">Upload a new photo</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-rose-500 group-hover:translate-x-1 transition-all" />
                </button>

                {analyses.length > 0 && (
                  <button
                    onClick={() => onNavigate('recommendations')}
                    className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-pink-50 transition-all text-left group"
                  >
                    <div className="bg-pink-100 w-10 h-10 rounded-xl flex items-center justify-center group-hover:bg-pink-200 transition-colors">
                      <Sparkles className="w-5 h-5 text-pink-500" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-gray-900">View Outfits</p>
                      <p className="text-xs text-gray-500">See your recommendations</p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-pink-500 group-hover:translate-x-1 transition-all" />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Center + Right — Analysis History */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl p-6 shadow-lg animate-fade-in-up" style={{ animationDelay: '200ms' }}>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-rose-500" />
                  <h3 className="font-bold text-gray-900 text-lg">Analysis History</h3>
                </div>
              </div>

              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="animate-shimmer h-20 rounded-xl" />
                  ))}
                </div>
              ) : analyses.length > 0 ? (
                <div className="space-y-3">
                  {analyses.map((analysis, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-4 p-4 rounded-xl border border-gray-100 hover:border-rose-200 hover:shadow-sm transition-all cursor-pointer group"
                      onClick={() => onAnalysisSelect ? onAnalysisSelect(analysis) : onNavigate('analysis')}
                    >
                      <div className="bg-gradient-to-br from-rose-100 to-pink-100 w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0">
                        <BarChart3 className="w-6 h-6 text-rose-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="text-sm font-semibold text-gray-900">
                            {analysis.body_shape || 'Body Shape'} • {analysis.skin_tone || 'Skin Tone'}
                          </p>
                          {analysis.confidence_score && (
                            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                              {Math.round(parseFloat(analysis.confidence_score) * 100)}%
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500">
                          {analysis.created_at ? getTimeAgo(analysis.created_at) : 'Unknown date'}
                        </p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-rose-500 group-hover:translate-x-1 transition-all flex-shrink-0" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="bg-gray-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                    <BarChart3 className="w-8 h-8 text-gray-400" />
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">No analyses yet</h4>
                  <p className="text-gray-500 text-sm mb-6">Upload your first photo to get personalized style insights</p>
                  <button
                    onClick={() => onNavigate('upload')}
                    className="bg-gradient-to-r from-rose-500 to-pink-500 text-white px-6 py-2.5 rounded-full text-sm font-medium hover:shadow-lg hover:shadow-rose-200 transition-all hover:scale-105"
                  >
                    Start Your First Analysis
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
