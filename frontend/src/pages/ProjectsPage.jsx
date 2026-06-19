import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FolderKanban, PlusCircle, Clock } from 'lucide-react';
import { apiFetch } from '../api/client';
import { formatRelativeTime } from '../lib/utils';

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchProjects = async () => {
    try {
      const res = await apiFetch('/projects');
      if (res.ok) {
        const data = await res.json();
        setProjects(data.projects || []);
      } else {
        setError('Failed to fetch projects');
      }
    } catch {
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      void fetchProjects();
    }, 0);

    return () => clearTimeout(timer);
  }, []);

  const createProject = async () => {
    try {
      const res = await apiFetch('/projects', {
        method: 'POST',
        body: JSON.stringify({ title: 'Untitled Property' }),
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
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="max-w-[1200px] mx-auto">
      <div className="flex items-end justify-between mb-10">
        <div>
          <h1 className="text-4xl font-black tracking-tight text-[#0F172A] mb-2">Projects</h1>
          <p className="text-lg text-[#64748B] font-medium">Manage your real estate generation workflows.</p>
        </div>
        <button onClick={createProject} className="bg-gradient-aurora text-white px-6 py-3 rounded-xl text-sm font-bold shadow-[0_10px_30px_rgba(14,165,233,0.3)] hover:scale-105 transition-transform active:scale-95 flex items-center gap-2">
          <PlusCircle size={18} /> New Project
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-100 text-red-600 px-5 py-4 rounded-2xl text-sm font-medium mb-8">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <div className="relative w-14 h-14">
            <div className="absolute inset-0 border-4 border-[#0EA5E9]/20 rounded-2xl animate-pulse"></div>
            <div className="absolute inset-0 border-4 border-[#0EA5E9] rounded-2xl border-t-transparent animate-spin"></div>
          </div>
          <p className="text-[#64748B] font-bold tracking-wider uppercase text-xs">Loading Projects</p>
        </div>
      ) : projects.length === 0 ? (
        <div className="rounded-[2rem] border-2 border-dashed border-[#E2E8F0] bg-white p-20 flex flex-col items-center justify-center text-center shadow-[0_20px_50px_rgba(0,0,0,0.02)]">
          <div className="w-20 h-20 rounded-full bg-[#F8FAFC] flex items-center justify-center mb-6 border border-[#E2E8F0]">
            <FolderKanban size={32} className="text-[#0EA5E9]" />
          </div>
          <h3 className="text-2xl font-black text-[#0F172A] mb-2">No projects yet</h3>
          <p className="text-[#64748B] font-medium max-w-sm mb-8">Start by creating a project to upload clips and generate your first property reel.</p>
          <button onClick={createProject} className="bg-[#0F172A] text-white px-8 py-4 rounded-xl font-bold shadow-lg hover:bg-[#1e293b] hover:-translate-y-0.5 transition-all">
            Create your first project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((p) => (
            <Link
              key={p._id}
              to={`/dashboard/projects/${p._id}`}
              className="glass-card rounded-2xl p-6 hover:-translate-y-1 hover:shadow-[0_30px_60px_rgba(0,0,0,0.06)] hover:border-[#0EA5E9]/30 transition-all group"
            >
              <div className="flex justify-between items-start mb-6">
                <div className="w-14 h-14 rounded-2xl bg-[#0EA5E9]/10 flex items-center justify-center group-hover:scale-110 group-hover:bg-gradient-aurora group-hover:text-white text-[#0EA5E9] transition-all shadow-sm">
                  <FolderKanban size={24} />
                </div>
                <div className="px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider bg-[#F8FAFC] border border-[#E2E8F0] text-[#64748B]">
                  {p.status}
                </div>
              </div>
              <h3 className="text-xl font-bold text-[#0F172A] truncate mb-2">{p.title}</h3>
              <p className="text-sm font-medium text-[#64748B] mb-6">{p.uploadCount || 0} raw clips · {p.generatedCount || 0} AI reels</p>
              
              <div className="flex items-center text-xs font-bold text-[#94a3b8] gap-1.5 mt-auto pt-4 border-t border-[#E2E8F0]">
                <Clock size={14} />
                Updated {formatRelativeTime(p.updatedAt)}
              </div>
            </Link>
          ))}
        </div>
      )}
    </motion.div>
  );
}
