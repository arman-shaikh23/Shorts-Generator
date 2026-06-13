import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Play, Sparkles, Layers, Zap, ArrowRight, Video } from 'lucide-react';

const features = [
  {
    icon: Sparkles,
    title: 'AI Scene Detection',
    desc: 'Automatically identifies rooms, amenities, and key property highlights from raw footage.',
  },
  {
    icon: Layers,
    title: 'Smart Story Builder',
    desc: 'AI arranges clips into a professional property walkthrough — Exterior → Living Room → Kitchen.',
  },
  {
    icon: Zap,
    title: 'Instant Rendering',
    desc: 'Generate cinematic vertical reels optimized for Instagram, TikTok, and YouTube Shorts in seconds.',
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] overflow-hidden selection:bg-[#0EA5E9]/20">
      
      {/* Top Nav */}
      <nav className="relative z-20 flex items-center justify-between max-w-7xl mx-auto px-6 py-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-aurora flex items-center justify-center shadow-lg shadow-[#0EA5E9]/20">
            <Play size={18} fill="white" className="ml-0.5 text-white" />
          </div>
          <span className="text-2xl font-extrabold tracking-tight">ReelForge</span>
        </div>
        <div className="flex items-center gap-6">
          <Link to="/login" className="text-[#64748B] hover:text-[#0F172A] transition text-sm font-bold">Sign In</Link>
          <Link to="/signup">
            <button className="bg-[#0F172A] text-white px-6 py-2.5 rounded-xl text-sm font-bold shadow-lg hover:bg-[#1e293b] transition-all hover:scale-105 active:scale-95">
              Get Started
            </button>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative flex flex-col items-center justify-center min-h-[85vh] px-6">
        
        {/* Abstract Aurora Background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-[-10%] left-[15%] w-[40%] h-[50%] bg-[#0EA5E9]/10 blur-[120px] rounded-full mix-blend-multiply" />
          <div className="absolute top-[20%] right-[10%] w-[35%] h-[45%] bg-[#14B8A6]/10 blur-[120px] rounded-full mix-blend-multiply" />
          <div className="absolute bottom-[-20%] left-[30%] w-[50%] h-[50%] bg-[#06B6D4]/10 blur-[140px] rounded-full mix-blend-multiply" />
        </div>

        <div className="relative z-10 text-center max-w-5xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <div className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white border border-[#E2E8F0] shadow-sm text-sm font-bold text-[#64748B] mb-8">
              <Sparkles size={16} className="text-[#0EA5E9]" />
              The AI-Powered Real Estate Studio
            </div>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }}
            className="text-6xl sm:text-7xl md:text-8xl lg:text-[100px] font-black tracking-tighter leading-[1.05] mb-8"
          >
            Property Reels.<br />
            <span className="text-gradient drop-shadow-sm">Zero Editing.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
            className="text-lg sm:text-2xl text-[#64748B] mb-12 font-medium max-w-3xl mx-auto leading-relaxed"
          >
            Upload raw clips from your phone. Our AI Director detects rooms, builds the perfect story, and renders cinematic social videos automatically.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
            className="flex flex-col sm:flex-row gap-5 justify-center items-center"
          >
            <Link to="/signup">
              <button className="bg-gradient-aurora text-white px-10 py-4 rounded-2xl text-lg font-bold shadow-[0_20px_50px_rgba(14,165,233,0.3)] hover:scale-105 transition-all active:scale-95 flex items-center gap-2">
                Start Creating Free <ArrowRight size={20} />
              </button>
            </Link>
            <Link to="/login">
              <button className="bg-white border-2 border-[#E2E8F0] text-[#0F172A] px-10 py-4 rounded-2xl text-lg font-bold shadow-sm hover:border-[#0EA5E9] transition-all flex items-center gap-2">
                <Video size={20} className="text-[#64748B]" /> View Demo
              </button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-32">
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-20">
          <h2 className="text-4xl sm:text-5xl font-black tracking-tight mb-6">Built for Luxury Marketing</h2>
          <p className="text-[#64748B] text-xl font-medium max-w-2xl mx-auto">Skip the complicated timelines. ReelForge generates premium assets in minutes.</p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="p-10 rounded-[2rem] bg-white border border-[#E2E8F0] hover:border-[#0EA5E9]/50 shadow-[0_20px_50px_rgba(0,0,0,0.03)] hover:shadow-[0_30px_60px_rgba(14,165,233,0.08)] transition-all duration-300 group hover:-translate-y-2"
            >
              <div className="w-16 h-16 rounded-2xl bg-[#F8FAFC] border border-[#E2E8F0] flex items-center justify-center mb-8 group-hover:bg-[#0EA5E9]/10 group-hover:border-[#0EA5E9]/20 transition-all">
                <f.icon size={28} className="text-[#64748B] group-hover:text-[#0EA5E9] transition-colors" />
              </div>
              <h3 className="text-2xl font-bold text-[#0F172A] mb-4">{f.title}</h3>
              <p className="text-[#64748B] font-medium leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#E2E8F0] py-12 text-center text-[#64748B] text-sm font-medium">
        <p>ReelForge AI — Premium real estate marketing automation.</p>
      </footer>
    </div>
  );
}
