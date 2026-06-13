import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Play, Sparkles, Layers, Zap, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/Button';

const features = [
  {
    icon: Sparkles,
    title: 'AI Scene Detection',
    desc: 'Automatically identifies rooms, amenities, and key property highlights from raw footage.',
  },
  {
    icon: Layers,
    title: 'Smart Story Builder',
    desc: 'AI arranges clips into a professional property walkthrough — Exterior → Living Room → Kitchen → Balcony.',
  },
  {
    icon: Zap,
    title: 'Instant Rendering',
    desc: 'Generate cinematic vertical reels optimized for Instagram, TikTok, and YouTube Shorts in seconds.',
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#050505] text-white overflow-hidden">
      {/* Nav */}
      <nav className="relative z-20 flex items-center justify-between max-w-6xl mx-auto px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
            <Play size={16} fill="white" className="ml-0.5" />
          </div>
          <span className="text-xl font-bold tracking-tight">ReelForge</span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/login" className="text-gray-400 hover:text-white transition text-sm font-medium">Sign In</Link>
          <Link to="/signup">
            <Button size="sm" variant="secondary">Get Started</Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative flex flex-col items-center justify-center min-h-[85vh] px-6">
        {/* Ambient Glows */}
        <div className="absolute top-[-20%] left-[10%] w-[40%] h-[40%] bg-blue-600/15 blur-[140px] rounded-full pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[5%] w-[35%] h-[35%] bg-indigo-600/15 blur-[140px] rounded-full pointer-events-none" />
        <div className="absolute top-[30%] right-[20%] w-[20%] h-[20%] bg-purple-600/10 blur-[100px] rounded-full pointer-events-none" />

        <div className="relative z-10 text-center max-w-4xl">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-gray-400 mb-8 backdrop-blur-sm">
              <Sparkles size={14} className="text-blue-400" />
              AI-Powered Real Estate Video Engine
            </div>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-extrabold tracking-tight leading-[1.05] mb-8"
          >
            Property Videos.{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-500">
              Viral Reels.
            </span>
            <br />
            <span className="text-gray-500">Zero Effort.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-lg sm:text-xl text-gray-400 mb-12 font-light max-w-2xl mx-auto leading-relaxed"
          >
            Upload raw property clips. Our AI detects rooms, builds a professional walkthrough,
            and renders cinematic social reels — ready for Instagram, TikTok, and YouTube.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex flex-col sm:flex-row gap-4 justify-center items-center"
          >
            <Link to="/signup">
              <Button size="xl" variant="primary">
                Start Creating Free
                <ArrowRight size={18} />
              </Button>
            </Link>
            <Link to="/login">
              <Button size="xl" variant="secondary">Sign In</Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="relative z-10 max-w-5xl mx-auto px-6 py-24">
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">Built for Real Estate Professionals</h2>
          <p className="text-gray-500 text-lg max-w-xl mx-auto">From raw footage to polished reels in under 2 minutes. No editing skills required.</p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="p-8 rounded-3xl bg-white/[0.03] border border-white/[0.06] hover:border-white/10 transition-all duration-300 group"
            >
              <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center mb-6 group-hover:bg-blue-500/20 transition">
                <f.icon size={22} className="text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold mb-3">{f.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center text-gray-600 text-sm">
        <p>ReelForge AI — Transforming real estate marketing.</p>
      </footer>
    </div>
  );
}
