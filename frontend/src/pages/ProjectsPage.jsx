import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Clock3,
  FolderKanban,
  Plus,
} from 'lucide-react';
import { apiFetch } from '../api/client';
import { formatRelativeTime } from '../lib/utils';

const PAGE_SIZE = 12;
const ease = [0.22, 1, 0.36, 1];

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

export default function ProjectsPage() {
  const prefersReducedMotion = useReducedMotion();
  const navigate = useNavigate();

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);

  const fetchProjects = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiFetch(`/projects?page=${page}&limit=${PAGE_SIZE}`);
      if (res.ok) {
        const data = await res.json();
        if ((data.pages || 0) > 0 && page > data.pages) {
          setPage(data.pages);
          return;
        }
        setProjects(data.projects || []);
        setTotal(data.total || 0);
        setPages(data.pages || 0);
        setHasNext(Boolean(data.has_next));
        setHasPrev(Boolean(data.has_prev));
      } else {
        setError('Failed to fetch projects.');
      }
    } catch {
      setError('Failed to connect to server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      void fetchProjects();
    }, 0);
    return () => clearTimeout(timer);
  }, [page]);

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

  const signals = useMemo(() => {
    const pageGenerated = projects.reduce((sum, p) => sum + Number(p.generatedCount || 0), 0);
    const pageUploads = projects.reduce((sum, p) => sum + Number(p.uploadCount || 0), 0);
    const activeDrafts = projects.filter((p) => String(p.status || '').toUpperCase().includes('DRAFT')).length;

    return [
      { label: 'Total Projects', value: total },
      { label: 'Uploads On Page', value: pageUploads },
      { label: 'Reels On Page', value: pageGenerated },
      { label: 'Drafts On Page', value: activeDrafts },
    ];
  }, [projects, total]);

  return (
    <div className="flex flex-col gap-8 pb-20">
      <motion.section
        initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease }}
        className="relative overflow-hidden rounded-[2rem] border border-[#dbe3f1] bg-white p-7 shadow-[0_26px_60px_rgba(15,23,42,0.08)] md:p-9"
      >
        <div className="pointer-events-none absolute -left-24 -top-20 h-56 w-56 rounded-full bg-[#0EA5E9]/12 blur-[80px]" />
        <div className="pointer-events-none absolute -right-20 bottom-[-4rem] h-56 w-56 rounded-full bg-[#14B8A6]/12 blur-[90px]" />

        <div className="relative grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-[#BFDBFE] bg-[#EFF6FF] px-3 py-1.5 text-[11px] font-extrabold uppercase tracking-[0.1em] text-[#0369A1]">
              <FolderKanban size={14} />
              Project Workspace
            </span>

            <h1 className="mt-4 font-['Sora'] text-4xl font-extrabold tracking-tight text-[#020617] md:text-5xl">
              Manage every reel pipeline from one clean project grid.
            </h1>
            <p className="mt-4 max-w-2xl text-base font-medium leading-relaxed text-[#475569] md:text-lg">
              Open drafts, track upload progress, and jump directly into storyboarding or final render in one click.
            </p>

            <div className="mt-7 flex flex-wrap items-center gap-3">
              <button
                onClick={createProject}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-aurora px-6 py-3.5 text-sm font-extrabold text-white shadow-[0_16px_34px_rgba(14,165,233,0.3)] transition hover:-translate-y-0.5 active:translate-y-0"
              >
                <Plus size={18} />
                New Project
              </button>
              <Link
                to="/dashboard/history"
                className="inline-flex items-center gap-2 rounded-xl border border-[#dbe3f1] bg-white px-5 py-3.5 text-sm font-bold text-[#0F172A] transition hover:border-[#93C5FD] hover:bg-[#F8FAFC]"
              >
                View Generated Reels
                <ArrowRight size={16} />
              </Link>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {signals.map((signal, index) => (
              <motion.div
                key={signal.label}
                initial={prefersReducedMotion ? false : { opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease, delay: prefersReducedMotion ? 0 : 0.08 + index * 0.05 }}
                className="rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-4 py-3.5"
              >
                <p className="font-['Sora'] text-2xl font-extrabold tracking-tight text-[#0F172A]">{signal.value}</p>
                <p className="mt-1 text-[11px] font-extrabold uppercase tracking-[0.08em] text-[#64748B]">{signal.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-semibold text-red-700">
          {error}
        </div>
      )}

      <motion.section
        initial={prefersReducedMotion ? false : { opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease, delay: prefersReducedMotion ? 0 : 0.08 }}
        className="rounded-[1.6rem] border border-[#dbe3f1] bg-white p-6 shadow-[0_20px_45px_rgba(15,23,42,0.06)]"
      >
        <div className="mb-5 flex items-center justify-between gap-3">
          <h2 className="font-['Sora'] text-xl font-extrabold tracking-tight text-[#0F172A]">Project Grid</h2>
          <span className="rounded-lg border border-[#e2e8f0] bg-[#f8fafc] px-3 py-1.5 text-xs font-extrabold uppercase tracking-[0.08em] text-[#475569]">
            Page {page} of {Math.max(1, pages)}
          </span>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="animate-pulse rounded-2xl border border-[#e2e8f0] bg-[#f8fafc] p-5">
                <div className="h-10 w-10 rounded-lg bg-[#e2e8f0]" />
                <div className="mt-4 h-4 w-36 rounded bg-[#e2e8f0]" />
                <div className="mt-2 h-3 w-24 rounded bg-[#e2e8f0]" />
                <div className="mt-5 h-3 w-28 rounded bg-[#e2e8f0]" />
              </div>
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="rounded-xl border-2 border-dashed border-[#e2e8f0] bg-[#f8fafc] px-6 py-12 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-white text-[#0284c7] shadow-sm">
              <FolderKanban size={24} />
            </div>
            <p className="text-xl font-extrabold tracking-tight text-[#0F172A]">No projects yet</p>
            <p className="mt-1 text-sm font-medium text-[#64748B]">Create your first project to start building reels.</p>
            <button
              onClick={createProject}
              className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#0F172A] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#1e293b]"
            >
              <Plus size={16} />
              Create Project
            </button>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {projects.map((project, index) => (
                <motion.div
                  key={project._id}
                  initial={prefersReducedMotion ? false : { opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35, ease, delay: prefersReducedMotion ? 0 : index * 0.03 }}
                >
                  <Link
                    to={`/dashboard/projects/${project._id}`}
                    className="group block rounded-2xl border border-[#e2e8f0] bg-[#f8fafc] p-5 transition hover:-translate-y-0.5 hover:border-[#bfdbfe] hover:bg-[#eff6ff]"
                  >
                    <div className="mb-4 flex items-center justify-between">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white text-[#0284c7] shadow-sm">
                        <FolderKanban size={20} />
                      </div>
                      <span
                        className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-[0.08em] ${getStatusTone(
                          project.status
                        )}`}
                      >
                        {project.status || 'Draft'}
                      </span>
                    </div>

                    <p className="truncate font-['Sora'] text-xl font-extrabold tracking-tight text-[#0F172A]">
                      {project.title || 'Untitled Property'}
                    </p>

                    <div className="mt-4 grid grid-cols-2 gap-2">
                      <div className="rounded-lg border border-[#e2e8f0] bg-white px-3 py-2">
                        <p className="text-base font-extrabold text-[#0F172A]">{project.uploadCount || 0}</p>
                        <p className="text-[10px] font-extrabold uppercase tracking-[0.08em] text-[#64748B]">Uploads</p>
                      </div>
                      <div className="rounded-lg border border-[#e2e8f0] bg-white px-3 py-2">
                        <p className="text-base font-extrabold text-[#0F172A]">{project.generatedCount || 0}</p>
                        <p className="text-[10px] font-extrabold uppercase tracking-[0.08em] text-[#64748B]">Reels</p>
                      </div>
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-[#e2e8f0] pt-3">
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#64748B]">
                        <Clock3 size={13} />
                        Updated {formatRelativeTime(project.updatedAt)}
                      </span>
                      <ArrowRight size={16} className="text-[#94a3b8] transition group-hover:translate-x-0.5 group-hover:text-[#0284c7]" />
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>

            <div className="mt-6 flex flex-col items-center justify-between gap-3 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-4 py-3 sm:flex-row">
              <p className="text-sm font-semibold text-[#64748B]">
                Showing {projects.length} of {total} projects.
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                  disabled={!hasPrev || loading}
                  className="inline-flex items-center gap-1 rounded-lg border border-[#dbe3f1] bg-white px-3.5 py-2 text-xs font-bold text-[#0F172A] transition hover:bg-[#eff6ff] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <ChevronLeft size={14} />
                  Prev
                </button>
                <button
                  onClick={() => setPage((prev) => prev + 1)}
                  disabled={!hasNext || loading}
                  className="inline-flex items-center gap-1 rounded-lg border border-[#dbe3f1] bg-white px-3.5 py-2 text-xs font-bold text-[#0F172A] transition hover:bg-[#eff6ff] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Next
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </>
        )}
      </motion.section>

      <motion.section
        initial={prefersReducedMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease, delay: prefersReducedMotion ? 0 : 0.14 }}
        className="grid gap-4 sm:grid-cols-3"
      >
        <Link
          to="/dashboard/projects"
          className="rounded-xl border border-[#bfdbfe] bg-[#eff6ff] px-4 py-3 transition hover:bg-[#dbeafe]"
        >
          <p className="text-sm font-extrabold text-[#0F172A]">Current Workspace</p>
          <p className="mt-0.5 text-xs font-semibold text-[#0369a1]">Project planning and upload control</p>
        </Link>
        <Link
          to="/dashboard/history"
          className="rounded-xl border border-[#d1fae5] bg-[#f0fdf4] px-4 py-3 transition hover:bg-[#dcfce7]"
        >
          <p className="text-sm font-extrabold text-[#0F172A]">Render Output</p>
          <p className="mt-0.5 text-xs font-semibold text-[#166534]">Review completed reels and downloads</p>
        </Link>
        <button
          type="button"
          onClick={createProject}
          className="text-left rounded-xl border border-[#fde68a] bg-[#fffbeb] px-4 py-3 transition hover:bg-[#fef3c7]"
        >
          <p className="text-sm font-extrabold text-[#0F172A]">Fast Start</p>
          <p className="mt-0.5 text-xs font-semibold text-[#92400e]">Create a new project instantly</p>
        </button>
      </motion.section>
    </div>
  );
}
