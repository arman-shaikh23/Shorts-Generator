import { useState } from 'react';
import {
  ArrowRight,
  Clapperboard,
  Scissors,
  Sparkles,
  TrendingUp,
  Type,
  Volume2,
  VolumeX,
} from 'lucide-react';

const workflowChips = ['22 Raw Clips', 'AI Analysis', 'Scene Selection', 'Final Reel'];

const featurePills = [
  { icon: Sparkles, label: 'AI Scene Detection', color: 'text-[#0EA5E9]' },
  { icon: Scissors, label: 'Duplicate Removal', color: 'text-[#F43F5E]' },
  { icon: Clapperboard, label: 'Story Sequencing', color: 'text-[#8B5CF6]' },
  { icon: Type, label: 'Auto Captions', color: 'text-[#10B981]' },
  { icon: TrendingUp, label: 'Viral Optimization', color: 'text-[#F59E0B]' },
];

export default function DemoVideoCard() {
  const [isMuted, setIsMuted] = useState(true);

  return (
    <div className="group relative mx-auto w-full max-w-[320px] transition-all duration-300 ease-out hover:-translate-y-1">
      <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-[#0EA5E9]/25 via-[#06B6D4]/25 to-[#14B8A6]/25 blur" />

      <div className="relative flex flex-col gap-3 overflow-hidden rounded-3xl border border-[#dbe3f1] bg-white/90 p-3 shadow-[0_24px_55px_rgba(15,23,42,0.1)] backdrop-blur">
        <div className="flex items-center justify-between px-1 pb-1">
          <div className="rounded-full border border-[#f97316]/25 bg-[#fff7ed] px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-[0.08em] text-[#ea580c]">
            Featured Demo
          </div>
          <div className="inline-flex items-center gap-1 rounded-full border border-[#0EA5E9]/25 bg-[#eff6ff] px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-[0.08em] text-[#0369a1]">
            <Sparkles size={10} />
            AI Powered
          </div>
        </div>

        <div className="group/video relative aspect-[9/16] w-full overflow-hidden rounded-2xl border border-[#dbe3f1] bg-[#020617] shadow-inner">
          <video
            className="h-full w-full object-cover transition-transform duration-500 group-hover/video:scale-105"
            src="/demo/how-it-works.mp4"
            autoPlay
            muted={isMuted}
            loop
            playsInline
            controlsList="nodownload noplaybackrate noremoteplayback"
            disablePictureInPicture
          />

          <button
            type="button"
            onClick={() => setIsMuted(!isMuted)}
            className="absolute right-3 top-3 rounded-full bg-black/65 p-2 text-white shadow-lg transition-colors hover:bg-black/85"
            aria-label={isMuted ? 'Unmute video' : 'Mute video'}
          >
            {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </button>

          <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/75 to-transparent p-3">
            <h3 className="text-sm font-bold text-white">See ReelForge in Action</h3>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-1.5 text-center">
          {workflowChips.map((chip, index) => (
            <div key={chip} className="inline-flex items-center gap-1">
              <span
                className={`rounded-md px-2 py-1 text-[9px] font-bold uppercase tracking-[0.08em] ${
                  index === workflowChips.length - 1
                    ? 'bg-gradient-aurora text-white'
                    : 'border border-[#e2e8f0] bg-[#f8fafc] text-[#475569]'
                }`}
              >
                {chip}
              </span>
              {index < workflowChips.length - 1 && <ArrowRight size={10} className="text-[#94a3b8]" />}
            </div>
          ))}
        </div>

        <div className="flex flex-wrap justify-center gap-1.5 pb-0.5">
          {featurePills.map((pill) => (
            <div
              key={pill.label}
              className="inline-flex items-center gap-1 rounded-md border border-[#e2e8f0] bg-[#f8fafc] px-2 py-1 text-[10px] font-semibold text-[#334155]"
            >
              <pill.icon size={11} className={pill.color} />
              {pill.label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
