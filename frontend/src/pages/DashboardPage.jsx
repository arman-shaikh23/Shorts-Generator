import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import {
  Activity,
  ArrowRight,
  Clock3,
  FolderKanban,
  Play,
  Plus,
  Sparkles,
  TrendingUp,
  Video,
} from 'lucide-react';
import { apiFetch, formatRelativeTime } from '../api/client';
import DemoVideoCard from '../components/dashboard/DemoVideoCard';
import { useToast } from '../context/ToastContext';

const ease = [0.22, 1, 0.36, 1];

const statConfig = [
  {
    key: 'projects',
    label: 'Active Projects',
    icon: FolderKanban,
    tone: 'text-[#0EA5E9]',
    bg: 'bg-[#EFF6FF]',
    border: 'border-[#BFDBFE]',
  },
  {
    key: 'videos',
    label: 'Raw Videos',
    icon: Video,
    tone: 'text-[#06B6D4]',
    bg: 'bg-[#ECFEFF]',
    border: 'border-[#A5F3FC]',
  },
  {
    key: 'scenes',
    label: 'AI Scenes',
    icon: Sparkles,
    tone: 'text-[#14B8A6]',
    bg: 'bg-[#F0FDFA]',
    border: 'border-[#99F6E4]',
  },
  {
    key: 'exported',
    label: 'Reels Exported',
    icon: Play,
    tone: 'text-[#10B981]',
    bg: 'bg-[#ECFDF5]',
    border: 'border-[#A7F3D0]',
  },
];

const quickActions = [
  {
    to: '/dashboard/projects',
    title: 'Open Projects',
    desc: 'Manage uploads and continue current edits.',
    icon: FolderKanban,
  },
  {
    to: '/dashboard/history',
    title: 'View Exports',
    desc: 'Review generated reels and download quickly.',
    icon: Play,
  },
];

function getStatusTone(status) {
  const normalized = String(status || '').toUpperCase();
  if (normalized.includes('DONE') || normalized.includes('SUCCESS') || normalized.includes('COMPLETED')) {
    return 'border-[#BBF7D0] bg-[#F0FDF4] text-[#166534]';
  }
  if (normalized.includes('ERROR') || normalized.includes('FAILED')) {
    return 'border-[#FECACA] bg-[#FEF2F2] text-[#B91C1C]';
  }
  if (normalized.includes('PROCESS') || normalized.includes('RUNNING')) {
    return 'border-[#BFDBFE] bg-[#EFF6FF] text-[#1D4ED8]';
  }
  return 'border-[#E2E8F0] bg-[#F8FAFC] text-[#475569]';
}

export default function DashboardPage() {
  const prefersReducedMotion = useReducedMotion();
  const navigate = useNavigate();
  const toast = useToast();

  const [stats, setStats] = useState({
    projects: 0,
    videos: 0,
    scenes: 0,
    exported: 0,
  });
  const [recentProjects, setRecentProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    async function fetchDashboardData() {
      setIsLoading(true);
      setError('');
      try {
        const [statsRes, projectsRes] = await Promise.all([
          apiFetch('/projects/dashboard/stats'),
          apiFetch('/projects?page=1&limit=4'),
        ]);

        if (!isMounted) return;

        if (statsRes.ok) {
          const data = await statsRes.json();
          setStats({
            projects: data.projects || 0,
            videos: data.videos || 0,
            scenes: data.scenes || 0,
            exported: data.exported || 0,
          });
        }

        if (projectsRes.ok) {
          const data = await projectsRes.json();
          setRecentProjects(data.projects || []);
        }

        if (!statsRes.ok && !projectsRes.ok) {
          setError('Failed to load dashboard data.');
        }
      } catch {
        if (isMounted) setError('Failed to connect to server.');
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    fetchDashboardData();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleCreateProject = async () => {
    try {
      const res = await apiFetch('/projects', {
        method: 'POST',
        body: JSON.stringify({ title: 'Untitled Reel' }),
      });
      if (res.ok) {
        const project = await res.json();
        toast.success('Project created', 'Opening project workspace.');
        navigate(`/dashboard/projects/${project._id}`);
      } else {
        toast.error('Create project failed', 'Please try again.');
      }
    } catch (err) {
      console.error(err);
      toast.error('Create project failed', 'Network or server issue.');
    }
  };

  const latestProject = recentProjects[0] || null;

  const productivitySignals = useMemo(() => {
    const clipsPerProject = stats.projects > 0 ? (stats.videos / stats.projects).toFixed(1) : '0.0';
    const scenesPerVideo = stats.videos > 0 ? (stats.scenes / stats.videos).toFixed(1) : '0.0';
    const exportRate = stats.projects > 0 ? Math.round((stats.exported / stats.projects) * 100) : 0;

    return [
      { label: 'Avg Clips / Project', value: clipsPerProject },
      { label: 'Avg Scenes / Video', value: scenesPerVideo },
      { label: 'Export Coverage', value: `${Math.max(0, exportRate)}%` },
    ];
  }, [stats]);

  return (
    <div className="flex flex-col gap-8 pb-20">
      <motion.section
        initial={prefersReducedMotion ? false : { opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease }}
        className="relative overflow-hidden rounded-[2rem] border border-[#dbe3f1] bg-white p-7 shadow-[0_26px_60px_rgba(15,23,42,0.08)] md:p-9"
      >
        <div className="pointer-events-none absolute -left-28 -top-24 h-64 w-64 rounded-full bg-[#0EA5E9]/12 blur-[80px]" />
        <div className="pointer-events-none absolute -right-24 bottom-[-4rem] h-64 w-64 rounded-full bg-[#14B8A6]/12 blur-[90px]" />

        <div className="relative grid gap-8 xl:grid-cols-[1.1fr_0.9fr] xl:items-center">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-[#BFDBFE] bg-[#EFF6FF] px-3 py-1.5 text-[11px] font-extrabold uppercase tracking-[0.1em] text-[#0369A1]">
              <Activity size={14} />
              Workspace Command Center
            </span>

            <h1 className="mt-4 max-w-3xl font-['Sora'] text-4xl font-extrabold tracking-tight text-[#020617] md:text-5xl">
              Build premium property reels with a faster, cleaner workflow.
            </h1>
            <p className="mt-4 max-w-2xl text-base font-medium leading-relaxed text-[#475569] md:text-lg">
              From one full home-tour upload to social-ready edits, this dashboard gives you quick control over projects,
              reel output, and production quality signals.
            </p>

            <div className="mt-7 flex flex-wrap items-center gap-3">
              <button
                onClick={handleCreateProject}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-aurora px-6 py-3.5 text-sm font-extrabold text-white shadow-[0_16px_34px_rgba(14,165,233,0.3)] transition hover:-translate-y-0.5 active:translate-y-0"
              >
                <Plus size={18} />
                Create New Reel
              </button>
              <Link
                to="/dashboard/projects"
                className="inline-flex items-center gap-2 rounded-xl border border-[#dbe3f1] bg-white px-5 py-3.5 text-sm font-bold text-[#0F172A] transition hover:border-[#93C5FD] hover:bg-[#F8FAFC]"
              >
                Go To Projects
                <ArrowRight size={16} />
              </Link>
              {latestProject && (
                <Link
                  to={`/dashboard/projects/${latestProject._id}`}
                  className="inline-flex items-center gap-2 rounded-xl border border-[#d1fae5] bg-[#f0fdf4] px-5 py-3.5 text-sm font-bold text-[#166534] transition hover:bg-[#dcfce7]"
                >
                  Continue Latest Project
                  <ArrowRight size={16} />
                </Link>
              )}
            </div>

            <div className="mt-7 grid gap-3 sm:grid-cols-3">
              {productivitySignals.map((signal) => (
                <div key={signal.label} className="rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-4 py-3">
                  <p className="font-['Sora'] text-lg font-bold tracking-tight text-[#0F172A]">{signal.value}</p>
                  <p className="mt-0.5 text-[11px] font-extrabold uppercase tracking-[0.08em] text-[#64748B]">{signal.label}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-center xl:justify-end">
            <DemoVideoCard />
          </div>
        </div>
      </motion.section>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-semibold text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <motion.section
          initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease, delay: prefersReducedMotion ? 0 : 0.08 }}
          className="rounded-[1.6rem] border border-[#dbe3f1] bg-white p-6 shadow-[0_20px_45px_rgba(15,23,42,0.06)]"
        >
          <div className="mb-5 flex items-center justify-between gap-3">
            <h2 className="font-['Sora'] text-xl font-extrabold tracking-tight text-[#0F172A]">Performance Snapshot</h2>
            <span className="text-xs font-extrabold uppercase tracking-[0.08em] text-[#64748B]">Live Metrics</span>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {isLoading
              ? Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="animate-pulse rounded-2xl border border-[#e2e8f0] bg-[#f8fafc] p-5">
                    <div className="h-4 w-24 rounded bg-[#e2e8f0]" />
                    <div className="mt-3 h-8 w-16 rounded bg-[#e2e8f0]" />
                  </div>
                ))
              : statConfig.map((stat) => (
                  <div
                    key={stat.key}
                    className={`group rounded-2xl border p-5 transition-all duration-300 hover:-translate-y-0.5 ${stat.border} ${stat.bg}`}
                  >
                    <div className="mb-4 flex items-center justify-between">
                      <div className={`flex h-11 w-11 items-center justify-center rounded-xl bg-white/80 ${stat.tone}`}>
                        <stat.icon size={20} />
                      </div>
                      <TrendingUp size={15} className="text-[#94a3b8]" />
                    </div>
                    <p className="font-['Sora'] text-3xl font-extrabold tracking-tight text-[#0F172A]">{stats[stat.key] || 0}</p>
                    <p className="mt-1 text-xs font-extrabold uppercase tracking-[0.1em] text-[#64748B]">{stat.label}</p>
                  </div>
                ))}
          </div>
        </motion.section>

        <motion.aside
          initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease, delay: prefersReducedMotion ? 0 : 0.14 }}
          className="rounded-[1.6rem] border border-[#dbe3f1] bg-white p-6 shadow-[0_20px_45px_rgba(15,23,42,0.06)]"
        >
          <h3 className="font-['Sora'] text-lg font-extrabold tracking-tight text-[#0F172A]">Quick Actions</h3>
          <div className="mt-4 space-y-3">
            {quickActions.map((action) => (
              <Link
                key={action.title}
                to={action.to}
                className="group flex items-start justify-between rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-4 py-3.5 transition hover:border-[#bfdbfe] hover:bg-[#eff6ff]"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-lg bg-white text-[#0284c7]">
                    <action.icon size={15} />
                  </div>
                  <div>
                    <p className="text-sm font-extrabold text-[#0F172A]">{action.title}</p>
                    <p className="mt-0.5 text-xs font-semibold text-[#64748B]">{action.desc}</p>
                  </div>
                </div>
                <ArrowRight size={15} className="mt-1 text-[#94a3b8] transition group-hover:translate-x-0.5 group-hover:text-[#0284c7]" />
              </Link>
            ))}
          </div>
        </motion.aside>
      </div>

      <motion.section
        initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease, delay: prefersReducedMotion ? 0 : 0.2 }}
        className="rounded-[1.6rem] border border-[#dbe3f1] bg-white p-6 shadow-[0_20px_45px_rgba(15,23,42,0.06)]"
      >
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-['Sora'] text-xl font-extrabold tracking-tight text-[#0F172A]">Recent Projects</h2>
            <p className="mt-1 text-sm font-medium text-[#64748B]">Jump back into your latest project timelines.</p>
          </div>
          <Link
            to="/dashboard/projects"
            className="inline-flex items-center gap-1.5 rounded-lg border border-[#e2e8f0] bg-[#f8fafc] px-3 py-2 text-xs font-extrabold uppercase tracking-[0.08em] text-[#334155] transition hover:border-[#bfdbfe] hover:bg-[#eff6ff] hover:text-[#0369a1]"
          >
            View All
            <ArrowRight size={14} />
          </Link>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="animate-pulse rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-4 py-4">
                <div className="h-4 w-40 rounded bg-[#e2e8f0]" />
                <div className="mt-2 h-3 w-24 rounded bg-[#e2e8f0]" />
              </div>
            ))}
          </div>
        ) : recentProjects.length === 0 ? (
          <div className="rounded-xl border-2 border-dashed border-[#e2e8f0] bg-[#f8fafc] px-6 py-10 text-center">
            <p className="text-base font-bold text-[#0F172A]">No projects yet</p>
            <p className="mt-1 text-sm font-medium text-[#64748B]">Create your first project to start generating reels.</p>
            <button
              onClick={handleCreateProject}
              className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[#0F172A] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#1e293b]"
            >
              <Plus size={16} />
              Create Project
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {recentProjects.map((project) => (
              <Link
                key={project._id}
                to={`/dashboard/projects/${project._id}`}
                className="group flex flex-col gap-4 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-4 py-4 transition hover:border-[#bfdbfe] hover:bg-[#eff6ff] md:flex-row md:items-center md:justify-between"
              >
                <div className="min-w-0">
                  <p className="truncate text-base font-bold tracking-tight text-[#0F172A]">
                    {project.title || 'Untitled Property'}
                  </p>
                  <p className="mt-1 text-xs font-semibold uppercase tracking-[0.08em] text-[#64748B]">
                    {(project.uploadCount || 0)} uploads - {(project.generatedCount || 0)} reels
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <span
                    className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-[0.08em] ${getStatusTone(
                      project.status
                    )}`}
                  >
                    {project.status || 'Draft'}
                  </span>
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#64748B]">
                    <Clock3 size={13} />
                    {formatRelativeTime(project.updatedAt)}
                  </span>
                  <ArrowRight size={16} className="text-[#94a3b8] transition group-hover:translate-x-0.5 group-hover:text-[#0284c7]" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </motion.section>
    </div>
  );
}
