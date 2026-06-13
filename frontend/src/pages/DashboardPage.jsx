import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Play, Video, LayoutTemplate, Activity, ChevronRight, Plus, FolderKanban, Sparkles } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { apiFetch } from '../api/client';
import { useAuth } from '../hooks/useAuth';

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    projects: 0,
    videos: 0,
    scenes: 0,
    exported: 0
  });

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await apiFetch('/projects/dashboard/stats');
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (err) {
        console.error("Failed to fetch dashboard stats", err);
      }
    }
    fetchStats();
  }, []);

  const navigate = useNavigate();

  const handleCreateProject = async () => {
    try {
      const res = await apiFetch('/projects', {
        method: 'POST',
        body: JSON.stringify({ title: 'Untitled Reel' }),
      });
      if (res.ok) {
        const project = await res.json();
        navigate(`/dashboard/projects/${project._id}`);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col gap-10 pb-20">
      
      {/* Hero Section */}
      <div className="relative rounded-[2rem] overflow-hidden bg-white shadow-[0_20px_50px_rgba(0,0,0,0.04)] border border-[#E2E8F0]">
        <div className="absolute inset-0 bg-gradient-aurora opacity-10"></div>
        <div className="relative px-12 py-16 md:py-24 max-w-4xl">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-[#0F172A] mb-6">
            Create Cinematic Property Reels <br/>
            <span className="text-gradient">with AI Intelligence</span>
          </h1>
          <p className="text-lg text-[#64748B] mb-10 max-w-2xl font-medium">
            Upload raw footage and let our AI Director build professional real-estate marketing videos automatically. Perfect sequencing, auto-captions, and trending audio.
          </p>
          <div className="flex items-center gap-4">
            <button onClick={handleCreateProject} className="bg-gradient-aurora text-white px-8 py-3.5 rounded-xl text-base font-bold shadow-lg shadow-[#0EA5E9]/20 hover:scale-105 transition-transform active:scale-95 flex items-center gap-2">
              <Plus size={20} /> Create New Reel
            </button>
            {/* <button className="bg-white border border-[#E2E8F0] text-[#0F172A] px-8 py-3.5 rounded-xl text-base font-bold shadow-sm hover:bg-[#F8FAFC] transition-colors flex items-center gap-2">
              <LayoutTemplate size={20} /> View Templates
            </button> */}
          </div>
        </div>
        
        {/* Decorative Floating Elements */}
        <div className="absolute right-0 top-0 bottom-0 w-1/3 hidden lg:flex items-center justify-center">
          <div className="w-64 h-64 bg-gradient-aurora rounded-full blur-[80px] opacity-20 animate-pulse"></div>
        </div>
      </div>

      {/* Stats Section */}
      <div>
        <h2 className="text-xl font-bold text-[#0F172A] mb-6 flex items-center gap-2">
          <Activity size={20} className="text-[#0EA5E9]" />
          Your Workspace Activity
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: 'Active Projects', value: stats.projects, icon: FolderKanban, color: 'text-[#0EA5E9]', bg: 'bg-[#0EA5E9]/10' },
            { label: 'Raw Videos Processed', value: stats.videos, icon: Video, color: 'text-[#06B6D4]', bg: 'bg-[#06B6D4]/10' },
            { label: 'AI Scenes Detected', value: stats.scenes, icon: Sparkles, color: 'text-[#14B8A6]', bg: 'bg-[#14B8A6]/10' },
            { label: 'Reels Exported', value: stats.exported, icon: Play, color: 'text-[#10B981]', bg: 'bg-[#10B981]/10' },
          ].map((stat, i) => (
            <div key={i} className="glass-card rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_30px_60px_rgba(0,0,0,0.06)] cursor-pointer">
              <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 rounded-2xl ${stat.bg} flex items-center justify-center`}>
                  <stat.icon size={24} className={stat.color} />
                </div>
                <ChevronRight size={20} className="text-[#64748B] opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <h3 className="text-3xl font-bold text-[#0F172A] mb-1">{stat.value}</h3>
              <p className="text-sm font-medium text-[#64748B] uppercase tracking-wider">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
