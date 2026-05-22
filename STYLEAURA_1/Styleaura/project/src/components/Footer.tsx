import { Sparkles, Heart } from 'lucide-react';

interface FooterProps {
  onNavigate: (page: string) => void;
}

export default function Footer({ onNavigate }: FooterProps) {
  const footerLinks = {
    product: [
      { label: 'Try It Now', page: 'upload' },
      { label: 'Outfits', page: 'recommendations' },
      { label: 'How It Works', page: 'about' },
    ],
    company: [
      { label: 'About Us', page: 'about' },
      { label: 'Contact', page: 'contact' },
    ],
    legal: [
      { label: 'Privacy Policy', page: 'home' },
      { label: 'Terms of Service', page: 'home' },
    ],
  };

  return (
    <footer className="bg-gray-900 text-gray-300 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="md:col-span-1">
            <div className="flex items-center space-x-2 mb-4">
              <div className="bg-gradient-to-br from-rose-400 to-pink-300 p-2 rounded-lg">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold text-white">StyleAura</span>
            </div>
            <p className="text-sm text-gray-400 mb-4">
              Your personal AI fashion advisor, helping you discover your perfect style.
            </p>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">Product</h3>
            <ul className="space-y-2">
              {footerLinks.product.map((link, index) => (
                <li key={index}>
                  <button
                    onClick={() => onNavigate(link.page)}
                    className="text-sm hover:text-rose-400 transition-colors"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">Company</h3>
            <ul className="space-y-2">
              {footerLinks.company.map((link, index) => (
                <li key={index}>
                  <button
                    onClick={() => onNavigate(link.page)}
                    className="text-sm hover:text-rose-400 transition-colors"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">Legal</h3>
            <ul className="space-y-2">
              {footerLinks.legal.map((link, index) => (
                <li key={index}>
                  <button
                    onClick={() => onNavigate(link.page)}
                    className="text-sm hover:text-rose-400 transition-colors"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <p className="text-sm text-gray-400">
            &copy; {new Date().getFullYear()} StyleAura. All rights reserved.
          </p>
          <p className="text-sm text-gray-400 flex items-center space-x-1">
            <span>Made with</span>
            <Heart className="w-4 h-4 text-rose-400 fill-rose-400" />
            <span>for fashion enthusiasts</span>
          </p>
        </div>
      </div>
    </footer>
  );
}
