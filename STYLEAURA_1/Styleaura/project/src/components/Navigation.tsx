import { Sparkles, Menu, X, User, LogOut, LayoutDashboard } from 'lucide-react';
import { useState, useEffect } from 'react';

interface NavigationProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  user?: any;
  onLogout?: () => void;
}

export default function Navigation({ currentPage, onNavigate, user, onLogout }: NavigationProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { id: 'home', label: 'Home' },
    { id: 'upload', label: 'Try It Now', protected: true },
    { id: 'recommendations', label: 'Outfits', protected: true },
    { id: 'about', label: 'About' },
    { id: 'contact', label: 'Contact' },
  ];

  const handleNavClick = (page: string) => {
    onNavigate(page);
    setMobileMenuOpen(false);
  };

  const handleLogout = () => {
    if (onLogout) {
      onLogout();
      setMobileMenuOpen(false);
    }
  };

  const filteredNavItems = navItems.filter(item => 
    !item.protected || user
  );

  return (
    <nav className={`sticky top-0 z-50 transition-all duration-300 ${
      scrolled 
        ? 'bg-white/90 backdrop-blur-xl shadow-sm border-b border-rose-100/50' 
        : 'bg-white/60 backdrop-blur-md border-b border-transparent'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <button
            onClick={() => handleNavClick('home')}
            className="flex items-center space-x-2 group"
          >
            <div className="bg-gradient-to-br from-rose-500 to-pink-500 p-2 rounded-xl group-hover:shadow-lg group-hover:shadow-rose-200 transition-all duration-300 group-hover:scale-105">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-rose-600 to-pink-500 bg-clip-text text-transparent" style={{ fontFamily: 'Outfit, sans-serif' }}>
              StyleAura
            </span>
          </button>

          <div className="hidden md:flex items-center space-x-1">
            {filteredNavItems.map((item) => (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  currentPage === item.id
                    ? 'bg-rose-50 text-rose-600 shadow-sm'
                    : 'text-gray-600 hover:text-rose-500 hover:bg-rose-50/50'
                }`}
              >
                {item.label}
              </button>
            ))}
            
            {/* Auth buttons */}
            <div className="ml-4 flex items-center space-x-2 border-l border-rose-100 pl-4">
              {user ? (
                <>
                  <button
                    onClick={() => handleNavClick('dashboard')}
                    className={`flex items-center space-x-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                      currentPage === 'dashboard'
                        ? 'bg-rose-50 text-rose-600 shadow-sm'
                        : 'text-gray-600 hover:text-rose-500 hover:bg-rose-50/50'
                    }`}
                  >
                    <LayoutDashboard className="w-4 h-4" />
                    <span>Dashboard</span>
                  </button>
                  <div className="flex items-center space-x-2 px-3 py-2 bg-gradient-to-r from-rose-50 to-pink-50 rounded-xl border border-rose-100/50">
                    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-rose-400 to-pink-400 flex items-center justify-center">
                      <span className="text-xs font-bold text-white">
                        {(user.first_name || user.email)?.[0]?.toUpperCase()}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-rose-700">
                      {user.first_name || user.email?.split('@')[0]}
                    </span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="p-2 rounded-xl text-gray-400 hover:text-rose-500 hover:bg-rose-50 transition-all duration-200"
                    title="Logout"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => handleNavClick('login')}
                    className="px-4 py-2 rounded-xl text-sm font-medium text-gray-600 hover:text-rose-500 hover:bg-rose-50 transition-all duration-200"
                  >
                    Login
                  </button>
                  <button
                    onClick={() => handleNavClick('signup')}
                    className="px-5 py-2 rounded-xl text-sm font-semibold bg-gradient-to-r from-rose-500 to-pink-500 text-white hover:shadow-lg hover:shadow-rose-200 transition-all duration-300 hover:scale-105"
                  >
                    Sign Up
                  </button>
                </>
              )}
            </div>
          </div>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-xl text-gray-600 hover:bg-rose-50 transition-colors"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-rose-100 animate-fade-in-down">
            {filteredNavItems.map((item) => (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`block w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  currentPage === item.id
                    ? 'bg-rose-50 text-rose-600'
                    : 'text-gray-600 hover:text-rose-500 hover:bg-rose-50/50'
                }`}
              >
                {item.label}
              </button>
            ))}
            
            {/* Mobile auth buttons */}
            <div className="border-t border-rose-100 mt-2 pt-2">
              {user ? (
                <>
                  <button
                    onClick={() => handleNavClick('dashboard')}
                    className="block w-full text-left px-4 py-3 rounded-xl text-sm font-medium text-gray-600 hover:text-rose-500 hover:bg-rose-50 transition-all"
                  >
                    <div className="flex items-center space-x-2">
                      <LayoutDashboard className="w-4 h-4" />
                      <span>Dashboard</span>
                    </div>
                  </button>
                  <div className="px-4 py-3 bg-rose-50 rounded-xl mb-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-rose-400 to-pink-400 flex items-center justify-center">
                        <span className="text-xs font-bold text-white">
                          {(user.first_name || user.email)?.[0]?.toUpperCase()}
                        </span>
                      </div>
                      <span className="text-sm font-medium text-rose-700">
                        {user.first_name || user.email?.split('@')[0]}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-3 rounded-xl text-sm font-medium text-gray-600 hover:text-rose-500 hover:bg-rose-50 transition-all"
                  >
                    <div className="flex items-center space-x-2">
                      <LogOut className="w-4 h-4" />
                      <span>Logout</span>
                    </div>
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => handleNavClick('login')}
                    className="block w-full text-left px-4 py-3 rounded-xl text-sm font-medium text-gray-600 hover:text-rose-500 hover:bg-rose-50 transition-all"
                  >
                    Login
                  </button>
                  <button
                    onClick={() => handleNavClick('signup')}
                    className="block w-full text-left px-4 py-3 rounded-xl text-sm font-medium bg-gradient-to-r from-rose-500 to-pink-500 text-white hover:shadow-lg transition-all mt-2"
                  >
                    Sign Up
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
