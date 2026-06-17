import React, { useState } from 'react';
import { Sparkles, Scissors, Clapperboard, Type, TrendingUp, ArrowRight, Volume2, VolumeX } from 'lucide-react';

export default function DemoVideoCard() {
  const [isMuted, setIsMuted] = useState(true);

  return (
    <div className="relative group w-full max-w-[280px] sm:max-w-[320px] mx-auto transition-all duration-300 ease-out hover:scale-[1.02]">
      {/* Background Glow / Premium Shadow */}
      <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-3xl blur opacity-25 group-hover:opacity-40 transition duration-300"></div>
      
      {/* Main Card Container */}
      <div className="relative bg-white/80 dark:bg-[#0F172A]/80 backdrop-blur-xl border border-white/20 dark:border-slate-700/50 rounded-3xl p-3 shadow-2xl overflow-hidden flex flex-col gap-3">
        
        {/* Header Badges */}
        <div className="flex items-center justify-between px-1 pb-1">
          <div className="flex items-center gap-1 text-[10px] font-bold px-2.5 py-1 bg-gradient-to-r from-orange-500/10 to-rose-500/10 text-orange-600 dark:text-orange-400 rounded-full border border-orange-500/20 shadow-sm">
            <span>🔥</span> Featured Demo
          </div>
          <div className="flex items-center gap-1 text-[10px] font-bold px-2.5 py-1 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 text-blue-600 dark:text-blue-400 rounded-full border border-blue-500/20 shadow-sm">
            <span>⚡</span> AI Powered
          </div>
        </div>

        {/* Video Player */}
        <div className="relative w-full aspect-[9/16] bg-black rounded-xl overflow-hidden border border-slate-100 dark:border-slate-800 shadow-inner group/video">
          <video 
            className="w-full h-full object-cover transition-transform duration-300 ease-out group-hover/video:scale-105"
            src="/demo/how-it-works.mp4"
            autoPlay
            muted={isMuted}
            loop
            playsInline
            controlsList="nodownload noplaybackrate noremoteplayback"
            disablePictureInPicture
          />
          
          {/* Custom Audio Toggle */}
          <button 
            onClick={() => setIsMuted(!isMuted)}
            className="absolute top-3 right-3 p-2 bg-black/60 hover:bg-black/80 backdrop-blur-md text-white rounded-full transition-colors shadow-lg z-20"
            aria-label={isMuted ? "Unmute video" : "Mute video"}
          >
            {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </button>
          {/* Overlay Title */}
          <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/80 to-transparent">
            <h3 className="text-white font-bold text-sm drop-shadow-md flex items-center gap-1.5">
              🎬 See ReelForge In Action
            </h3>
          </div>
        </div>

        {/* Workflow Steps */}
        <div className="flex flex-col items-center justify-center py-1 text-[10px] sm:text-[11px] font-medium text-slate-600 dark:text-slate-300">
          <div className="flex flex-wrap items-center justify-center gap-1 w-full text-center leading-tight">
            <div className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-[9px] sm:text-[10px]">22 Raw Clips</div>
            <ArrowRight size={10} className="text-slate-400 hidden sm:block" />
            <div className="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded text-[9px] sm:text-[10px]">AI Analysis</div>
            <ArrowRight size={10} className="text-slate-400 hidden sm:block" />
            <div className="px-1.5 py-0.5 bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded text-[9px] sm:text-[10px]">Scene Selection</div>
            <ArrowRight size={10} className="text-slate-400 hidden sm:block" />
            <div className="px-1.5 py-0.5 bg-gradient-aurora text-white rounded shadow-sm font-bold mt-1 sm:mt-0 text-[9px] sm:text-[10px]">Cinematic Reel</div>
          </div>
          <div className="mt-2 text-[9px] sm:text-[10px] font-bold text-emerald-500 bg-emerald-50 dark:bg-emerald-500/10 px-3 py-1 rounded-full shadow-sm">
            Generated in under 2 minutes
          </div>
        </div>

        {/* Feature Badges */}
        <div className="flex flex-wrap justify-center gap-1.5 pb-1">
          <div className="flex items-center gap-1 text-[9px] sm:text-[10px] font-semibold px-2 py-1 bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300 rounded-md border border-slate-200 dark:border-slate-700">
            <Sparkles size={10} className="text-blue-500" /> AI Scene Detection
          </div>
          <div className="flex items-center gap-1 text-[9px] sm:text-[10px] font-semibold px-2 py-1 bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300 rounded-md border border-slate-200 dark:border-slate-700">
            <Scissors size={10} className="text-rose-500" /> Duplicate Removal
          </div>
          <div className="flex items-center gap-1 text-[9px] sm:text-[10px] font-semibold px-2 py-1 bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300 rounded-md border border-slate-200 dark:border-slate-700">
            <Clapperboard size={10} className="text-purple-500" /> Cinematic Storytelling
          </div>
          <div className="flex items-center gap-1 text-[9px] sm:text-[10px] font-semibold px-2 py-1 bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300 rounded-md border border-slate-200 dark:border-slate-700">
            <Type size={10} className="text-emerald-500" /> Auto Captions
          </div>
          <div className="flex items-center gap-1 text-[9px] sm:text-[10px] font-semibold px-2 py-1 bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300 rounded-md border border-slate-200 dark:border-slate-700">
            <TrendingUp size={10} className="text-orange-500" /> Viral Reel
          </div>
        </div>
        
      </div>
    </div>
  );
}
