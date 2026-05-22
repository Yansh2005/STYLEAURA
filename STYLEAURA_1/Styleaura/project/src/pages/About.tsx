import { Target, Users, Sparkles, Award } from 'lucide-react';

interface AboutProps {
  onNavigate: (page: string) => void;
}

export default function About({ onNavigate }: AboutProps) {
  const values = [
    {
      icon: <Target className="w-6 h-6" />,
      title: 'Our Mission',
      description:
        'To democratize fashion by making personalized style advice accessible to everyone through cutting-edge AI technology.',
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: 'Community First',
      description:
        'Building a supportive community where everyone can discover and express their unique style with confidence.',
    },
    {
      icon: <Sparkles className="w-6 h-6" />,
      title: 'Innovation',
      description:
        'Leveraging the latest in AI and machine learning to deliver accurate, insightful fashion recommendations.',
    },
    {
      icon: <Award className="w-6 h-6" />,
      title: 'Excellence',
      description:
        'Committed to providing the highest quality style analysis and recommendations for every user.',
    },
  ];

  const stats = [
    { number: '50K+', label: 'Happy Users' },
    { number: '1M+', label: 'Outfits Analyzed' },
    { number: '95%', label: 'Satisfaction Rate' },
    { number: '24/7', label: 'AI Availability' },
  ];

  return (
    <div className="min-h-screen bg-white">
      <section className="bg-gradient-to-br from-rose-50 via-pink-50 to-orange-50 py-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            About
            <span className="block bg-gradient-to-r from-rose-500 via-pink-500 to-orange-400 bg-clip-text text-transparent">
              StyleAura
            </span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Empowering individuals to discover their perfect style through the power of
            artificial intelligence and personalized fashion insights.
          </p>
        </div>
      </section>

      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-20">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-rose-500 to-pink-500 bg-clip-text text-transparent mb-2">
                  {stat.number}
                </div>
                <div className="text-gray-600 font-medium">{stat.label}</div>
              </div>
            ))}
          </div>

          <div className="mb-20">
            <div className="max-w-4xl mx-auto text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                Our Story
              </h2>
              <div className="space-y-4 text-lg text-gray-600 text-left">
                <p>
                  StyleAura was born from a simple belief: everyone deserves access to
                  personalized fashion advice. Traditional styling services are often
                  expensive and inaccessible, leaving many people struggling to find their
                  perfect style.
                </p>
                <p>
                  We combined our passion for fashion with cutting-edge AI technology to
                  create a platform that analyzes your unique features, preferences, and
                  lifestyle to deliver personalized outfit recommendations that truly reflect
                  who you are.
                </p>
                <p>
                  Today, StyleAura serves thousands of fashion enthusiasts worldwide, helping
                  them discover their style confidence and express themselves through fashion.
                </p>
              </div>
            </div>
          </div>

          <div className="mb-20">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 text-center mb-12">
              Our Values
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {values.map((value, index) => (
                <div
                  key={index}
                  className="bg-gradient-to-br from-rose-50 to-pink-50 p-6 rounded-2xl hover:shadow-lg transition-all"
                >
                  <div className="bg-white w-14 h-14 rounded-xl flex items-center justify-center text-rose-500 mb-4 shadow-sm">
                    {value.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">
                    {value.title}
                  </h3>
                  <p className="text-gray-600">{value.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="bg-gradient-to-br from-rose-500 to-pink-500 py-20 px-4 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to Discover Your Style?
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Join thousands of users who have already found their perfect fashion aesthetic
          </p>
          <button
            onClick={() => onNavigate('upload')}
            className="bg-white text-rose-600 px-10 py-4 rounded-full font-medium text-lg hover:shadow-xl transition-all hover:scale-105"
          >
            Get Started Today
          </button>
        </div>
      </section>
    </div>
  );
}
