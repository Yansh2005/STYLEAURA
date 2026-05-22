import { useState, useEffect } from 'react';
import Navigation from './components/Navigation';
import Footer from './components/Footer';
import Home from './pages/Home';
import ImageUpload from './pages/ImageUpload';
import AnalysisResult from './pages/AnalysisResult';
import OutfitRecommendations from './pages/OutfitRecommendations';
import About from './pages/About';
import Contact from './pages/Contact';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [user, setUser] = useState(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [recommendationsData, setRecommendationsData] = useState<any>(null);
  const [userPhotoUrl, setUserPhotoUrl] = useState<string | null>(null);
  const [pageKey, setPageKey] = useState(0);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setPageKey(prev => prev + 1);
  }, [currentPage]);

  useEffect(() => {
    // Check if user is logged in on app load
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      try {
        setUser(JSON.parse(userData));
      } catch (error) {
        console.error('Error parsing user data:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
      }
    }

    // Restore analysis from sessionStorage (photo is kept in state only — too large for sessionStorage)
    sessionStorage.removeItem('user_photo_url'); // evict any stale large photo from previous versions
    const savedAnalysis = sessionStorage.getItem('analysis_data');
    const savedRecs = sessionStorage.getItem('recommendations_data');
    if (savedAnalysis) {
      try { setAnalysisData(JSON.parse(savedAnalysis)); } catch {}
    }
    if (savedRecs) {
      try { setRecommendationsData(JSON.parse(savedRecs)); } catch {}
    }
  }, []);

  const handleNavigate = (page: string) => {
    setCurrentPage(page);
  };

  const handleLogin = (userData: any) => {
    setUser(userData);
  };

  const handleLogout = () => {
    setUser(null);
    setAnalysisData(null);
    setRecommendationsData(null);
    setUserPhotoUrl(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('analysis_data');
    sessionStorage.removeItem('recommendations_data');
    setCurrentPage('home');
  };

  const handleAnalysisComplete = (analysis: any, recommendations: any, photoUrl?: string) => {
    setAnalysisData(analysis);
    setRecommendationsData(recommendations);
    if (photoUrl) {
      setUserPhotoUrl(photoUrl);  // kept in state only — base64 is too large for sessionStorage
    }
    sessionStorage.setItem('analysis_data', JSON.stringify(analysis));
    sessionStorage.setItem('recommendations_data', JSON.stringify(recommendations));
    setCurrentPage('analysis');
  };

  // Called by any "Upload New Photo" button — clears old analysis before navigating
  const handleNewUpload = () => {
    setAnalysisData(null);
    setRecommendationsData(null);
    setUserPhotoUrl(null);
    sessionStorage.removeItem('analysis_data');
    sessionStorage.removeItem('recommendations_data');
    setCurrentPage('upload');
  };

  // Called when user clicks a history item in Dashboard
  const handleAnalysisSelect = (analysis: any) => {
    // Rebuild the analysis + recommendations from the stored record
    setAnalysisData(analysis);
    // Reconstruct recommendations from what was stored in the analysis
    const { body_shape, skin_tone, detected_gender, color_palette } = analysis;
    if (body_shape && skin_tone) {
      // Store in sessionStorage so AnalysisResult page can read it
      sessionStorage.setItem('analysis_data', JSON.stringify(analysis));
      // We don't have full recommendations stored, so clear them
      // so AnalysisResult shows the analysis info without outfits
      setRecommendationsData(null);
      sessionStorage.removeItem('recommendations_data');
    }
    setUserPhotoUrl(null);
    sessionStorage.removeItem('user_photo_url');
    setCurrentPage('analysis');
  };

  const renderPage = () => {
    // If user is not logged in and trying to access protected pages, redirect to login
    const protectedPages = ['upload', 'analysis', 'recommendations', 'dashboard'];
    if (!user && protectedPages.includes(currentPage)) {
      return <Login onNavigate={handleNavigate} onLogin={handleLogin} />;
    }

    switch (currentPage) {
      case 'home':
        return <Home onNavigate={handleNavigate} />;
      case 'login':
        return <Login onNavigate={handleNavigate} onLogin={handleLogin} />;
      case 'signup':
        return <Signup onNavigate={handleNavigate} onLogin={handleLogin} />;
      case 'upload':
        return <ImageUpload onNavigate={handleNavigate} onAnalysisComplete={handleAnalysisComplete} />;
      case 'analysis':
        return (
          <AnalysisResult 
            onNavigate={handleNavigate} 
            analysisData={analysisData} 
            recommendationsData={recommendationsData}
            userPhotoUrl={userPhotoUrl}
          />
        );
      case 'recommendations':
        return (
          <OutfitRecommendations 
            onNavigate={handleNavigate}
            onNewUpload={handleNewUpload}
            analysisData={analysisData}
            recommendationsData={recommendationsData}
            userPhotoUrl={userPhotoUrl}
          />
        );
      case 'dashboard':
        return <Dashboard onNavigate={handleNavigate} onAnalysisSelect={handleAnalysisSelect} user={user} />;
      case 'about':
        return <About onNavigate={handleNavigate} />;
      case 'contact':
        return <Contact />;
      default:
        return <Home onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <Navigation 
        currentPage={currentPage} 
        onNavigate={handleNavigate} 
        user={user}
        onLogout={handleLogout}
      />
      <main>
        <div key={pageKey} className="page-transition">
          {renderPage()}
        </div>
      </main>
      <Footer onNavigate={handleNavigate} />
    </div>
  );
}

export default App;
