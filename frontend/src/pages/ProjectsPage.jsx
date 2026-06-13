import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FolderKanban, PlusCircle, MoreVertical, Clock } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { apiFetch } from '../api/client';
import { formatRelativeTime } from '../lib/utils';

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const res = await apiFetch('/projects');
      if (res.ok) {
        const data = await res.json();
        setProjects(data.projects || []);
      } else {
        setError('Failed to fetch projects');
      }
    } catch (err) {
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
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
      <div className="flex items-end justify-between mb-10">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-1">Projects</h1>
          <p className="text-gray-500">Manage your real estate generation workflows.</p>
        </div>
        <Button variant="primary" size="md" onClick={createProject}>
          <PlusCircle size={18} />
          New Project
        </Button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 px-4 py-3 rounded-xl text-sm mb-6">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : projects.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-white/10 p-16 flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-6">
            <FolderKanban size={28} className="text-gray-500" />
          </div>
          <h3 className="text-xl font-bold mb-2">No projects yet</h3>
          <p className="text-gray-500 max-w-sm mb-8">Start by creating a project to upload clips and generate your first property reel.</p>
          <Button variant="primary" onClick={createProject}>
            Create your first project
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((p) => (
            <Link
              key={p._id}
              to={`/dashboard/projects/${p._id}`}
              className="bg-[#111] border border-white/10 rounded-2xl p-6 hover:border-white/20 hover:bg-white/[0.03] transition group"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center group-hover:scale-105 transition">
                  <FolderKanban size={20} className="text-blue-400" />
                </div>
                <div className="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider bg-white/5 text-gray-400">
                  {p.status}
                </div>
              </div>
              <h3 className="text-lg font-bold truncate mb-1">{p.title}</h3>
              <p className="text-sm text-gray-500 mb-6">{p.uploadCount || 0} clips · {p.generatedCount || 0} reels</p>
              
              <div className="flex items-center text-xs text-gray-600 gap-1.5 mt-auto pt-4 border-t border-white/5">
                <Clock size={12} />
                Updated {formatRelativeTime(p.updatedAt)}
              </div>
            </Link>
          ))}
        </div>
      )}
    </motion.div>
  );
}
