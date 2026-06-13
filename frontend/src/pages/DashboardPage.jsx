import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PlusCircle, FolderKanban, Clock } from 'lucide-react';
import { GlowCard } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { apiFetch } from '../api/client';
import { formatRelativeTime } from '../lib/utils';
import { useAuth } from '../hooks/useAuth';

export default function DashboardPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [stats, setStats] = useState({ totalProjects: 0, totalShorts: 0, hoursSaved: 0 });
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const res = await apiFetch('/projects?limit=3');
      if (res.ok) {
        const data = await res.json();
        setProjects(data.projects || []);
        
        // Calculate rough stats
        const totalProjs = data.total || 0;
        const totalShorts = (data.projects || []).reduce((acc, p) => acc + (p.generatedCount || 0), 0);
        // Estimate 2 hours saved per generated short
        const hoursSaved = totalShorts * 2;
        
        setStats({ totalProjects: totalProjs, totalShorts, hoursSaved });
      }
    } catch (err) {
      console.error('Failed to fetch dashboard data', err);
    }
  };

  const createProject = async () => {
    try {
      const res = await apiFetch('/projects', {
        method: 'POST',
        body: JSON.stringify({ title: 'Untitled Project' }),
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
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      {/* Header */}
      <div className="flex items-end justify-between mb-12">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-1">Workspace</h1>
          <p className="text-gray-500">Welcome back, {user?.name || 'Creator'}.</p>
        </div>
        <Button variant="primary" size="md" onClick={createProject}>
          <PlusCircle size={18} />
          New Project
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-14">
        <GlowCard color="blue">
          <p className="text-gray-500 text-sm font-medium mb-1">Total Projects</p>
          <p className="text-4xl font-light tracking-tight">{stats.totalProjects}</p>
        </GlowCard>
        <GlowCard color="purple">
          <p className="text-gray-500 text-sm font-medium mb-1">Shorts Generated</p>
          <p className="text-4xl font-light tracking-tight">{stats.totalShorts}</p>
        </GlowCard>
        <GlowCard color="green">
          <p className="text-gray-500 text-sm font-medium mb-1">Hours Saved</p>
          <p className="text-4xl font-light tracking-tight text-green-400">{stats.hoursSaved}</p>
        </GlowCard>
      </div>

      {/* Recent Projects */}
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-semibold tracking-tight">Recent Projects</h2>
        <Link to="/dashboard/projects" className="text-sm text-gray-500 hover:text-white transition">View all →</Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* Create New Card */}
        <div
          onClick={createProject}
          className="rounded-2xl border border-dashed border-white/10 p-12 flex flex-col items-center justify-center text-gray-600 hover:text-blue-400 hover:border-blue-500/40 hover:bg-blue-500/5 transition-all duration-300 cursor-pointer group"
        >
          <PlusCircle size={32} className="mb-3 opacity-50 group-hover:opacity-100 transition" />
          <p className="font-medium text-sm">Create a project</p>
        </div>

        {/* Real Projects */}
        {projects.map((p) => (
          <Link
            key={p._id}
            to={`/dashboard/projects/${p._id}`}
            className="bg-[#111] border border-white/10 rounded-2xl p-6 hover:border-white/20 hover:bg-white/[0.03] transition group flex flex-col h-full"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center group-hover:scale-105 transition">
                <FolderKanban size={18} className="text-blue-400" />
              </div>
            </div>
            <h3 className="text-base font-bold truncate mb-1">{p.title}</h3>
            <p className="text-xs text-gray-500 mb-6">{p.uploadCount || 0} clips</p>
            
            <div className="flex items-center text-[11px] text-gray-600 gap-1.5 mt-auto pt-4 border-t border-white/5">
              <Clock size={12} />
              {formatRelativeTime(p.updatedAt)}
            </div>
          </Link>
        ))}
      </div>
    </motion.div>
  );
}
