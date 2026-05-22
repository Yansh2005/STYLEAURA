import { Sparkles, Wand2, Heart, Zap, Upload, Eye, ShoppingBag, ArrowRight, ChevronRight } from 'lucide-react';

interface HomeProps {
  onNavigate: (page: string) => void;
}

export default function Home({ onNavigate }: HomeProps) {
  const features = [
    {
      icon: <Sparkles className="w-6 h-6" />,
      title: 'AI-Powered Analysis',
      description: 'Advanced ML algorithms analyze your skin tone and body shape for precise recommendations',
      gradient: 'from-rose-500 to-pink-500',
    },
    {
      icon: <Wand2 className="w-6 h-6" />,
      title: 'Personalized Outfits',
      description: 'Get curated outfit sets tailored to your unique body shape and color palette',
      gradient: 'from-pink-500 to-purple-500',
    },
    {
      icon: <Heart className="w-6 h-6" />,
      title: 'Style Discovery',
      description: 'Explore fashion trends that match your aesthetic with occasion-based filters',
      gradient: 'from-orange-500 to-rose-500',
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: 'Instant Results',
      description: 'Upload a photo and receive fashion insights in under 15 seconds',
      gradient: 'from-amber-500 to-orange-500',
    },
  ];

  const steps = [
    { num: '01', icon: <Upload className="w-7 h-7" />, title: 'Upload Your Photo', desc: 'Take a full-body photo or upload an existing one' },
    { num: '02', icon: <Eye className="w-7 h-7" />, title: 'AI Analyzes You', desc: 'Our ML detects your skin tone, body shape & proportions' },
    { num: '03', icon: <ShoppingBag className="w-7 h-7" />, title: 'Get Styled', desc: 'Receive personalized outfits, colors & shopping links' },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-rose-50 via-pink-50 to-orange-50 py-20 md:py-28 px-4 overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-20 left-10 w-64 h-64 bg-rose-200/30 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-10 right-10 w-80 h-80 bg-pink-200/30 rounded-full blur-3xl animate-float" style={{ animationDelay: '1.5s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-orange-100/20 rounded-full blur-3xl" />

        <div className="max-w-7xl mx-auto text-center relative z-10">
          <div className="inline-block mb-5 animate-fade-in-up">
            <span className="bg-white/80 backdrop-blur text-rose-600 px-5 py-2 rounded-full text-sm font-semibold border border-rose-200 shadow-sm inline-flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              AI-Powered Personal Fashion Advisor
            </span>
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold text-gray-900 mb-6 animate-fade-in-up" style={{ fontFamily: 'Outfit, sans-serif', animationDelay: '100ms' }}>
            Discover Your
            <span className="block gradient-text animate-gradient">
              Perfect Style
            </span>
          </h1>

          <p className="text-lg md:text-xl text-gray-600 mb-10 max-w-2xl mx-auto animate-fade-in-up leading-relaxed" style={{ animationDelay: '200ms' }}>
            Upload your photo and let our AI analyze your skin tone & body shape. Get personalized outfit
            recommendations with curated color palettes — in seconds.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up" style={{ animationDelay: '300ms' }}>
            <button
              onClick={() => onNavigate('upload')}
              className="bg-gradient-to-r from-rose-500 to-pink-500 text-white px-9 py-4 rounded-full font-semibold text-lg hover:shadow-2xl hover:shadow-rose-300/40 transition-all hover:scale-105 active:scale-95 inline-flex items-center gap-2 group"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={() => onNavigate('about')}
              className="bg-white/80 backdrop-blur text-gray-700 px-9 py-4 rounded-full font-semibold text-lg border-2 border-gray-200 hover:border-rose-300 hover:text-rose-600 transition-all"
            >
              Learn More
            </button>
          </div>
        </div>
      </section>

      {/* Video Showcase */}
      <section className="py-20 md:py-24 px-4 bg-gradient-to-b from-rose-50/60 via-white to-white relative overflow-hidden">
        {/* Decorative blurs */}
        <div className="absolute top-0 left-1/4 w-72 h-72 bg-pink-100/40 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-72 h-72 bg-orange-100/40 rounded-full blur-3xl" />

        <div className="max-w-5xl mx-auto relative z-10">
          <div className="text-center mb-12">
            <span className="text-rose-500 font-semibold text-sm uppercase tracking-wider">See It In Action</span>
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mt-3 mb-4" style={{ fontFamily: 'Outfit, sans-serif' }}>
              Watch StyleAura Work
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto text-lg">
              Experience how our AI transforms a simple photo into a complete personalized style guide
            </p>
          </div>

          <div className="relative group">
            {/* Glow behind video */}
            <div className="absolute -inset-4 bg-gradient-to-r from-rose-300/30 via-pink-300/30 to-orange-300/30 rounded-[2rem] blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />

            <div className="relative bg-white rounded-2xl shadow-2xl shadow-rose-200/30 border border-gray-100 overflow-hidden">
              <video
                className="w-full h-auto rounded-2xl"
                autoPlay
                muted
                loop
                playsInline
                controls
                preload="metadata"
              >
                <source src="/styleaura-demo.mp4" type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 md:py-24 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-rose-500 font-semibold text-sm uppercase tracking-wider">Simple Process</span>
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mt-3 mb-4" style={{ fontFamily: 'Outfit, sans-serif' }}>
              How It Works
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto text-lg">
              Three simple steps to discover your personalized style profile
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-0 relative stagger-children">
            {/* Connecting line (desktop only) */}
            <div className="hidden md:block absolute top-16 left-[20%] right-[20%] h-0.5 bg-gradient-to-r from-rose-200 via-pink-200 to-orange-200" />
            
            {steps.map((step, index) => (
              <div key={index} className="relative text-center px-6">
                <div className="relative inline-block mb-6">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-rose-500 to-pink-500 flex items-center justify-center text-white shadow-xl shadow-rose-200/50 mx-auto relative z-10">
                    {step.icon}
                  </div>
                  <span className="absolute -top-2 -right-2 bg-white text-rose-500 text-xs font-bold w-7 h-7 rounded-full flex items-center justify-center border-2 border-rose-200 z-20 shadow-sm">
                    {step.num}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{step.title}</h3>
                <p className="text-gray-500 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 md:py-24 px-4 bg-gradient-to-br from-gray-50 to-rose-50/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-rose-500 font-semibold text-sm uppercase tracking-wider">Features</span>
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mt-3 mb-4" style={{ fontFamily: 'Outfit, sans-serif' }}>
              Why Choose StyleAura
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 stagger-children">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-white p-7 rounded-2xl shadow-sm border border-gray-100 card-hover group"
              >
                <div className={`bg-gradient-to-br ${feature.gradient} w-14 h-14 rounded-xl flex items-center justify-center text-white mb-5 shadow-lg group-hover:scale-110 transition-transform`}>
                  {feature.icon}
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-500 text-sm leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 md:py-24 px-4 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gradient-to-r from-rose-500 via-pink-500 to-rose-600 rounded-3xl p-10 md:p-16 text-center text-white shadow-2xl shadow-rose-300/30 relative overflow-hidden">
            {/* Decorative */}
            <div className="absolute top-0 right-0 w-40 h-40 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/10 rounded-full translate-y-1/2 -translate-x-1/2" />
            
            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ fontFamily: 'Outfit, sans-serif' }}>
                Ready to Transform Your Style?
              </h2>
              <p className="text-xl mb-10 opacity-90 max-w-xl mx-auto">
                Join thousands of fashion enthusiasts who discovered their perfect look with AI
              </p>
              <button
                onClick={() => onNavigate('upload')}
                className="bg-white text-rose-600 px-10 py-4 rounded-full font-bold text-lg hover:shadow-2xl transition-all hover:scale-105 active:scale-95 inline-flex items-center gap-2 group"
              >
                Start Your Journey
                <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
