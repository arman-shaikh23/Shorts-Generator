import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Clock3,
  FolderKanban,
  Plus,
  Search,
} from 'lucide-react';
import { apiFetch } from '../api/client';
import { formatRelativeTime } from '../lib/utils';
import { useToast } from '../context/ToastContext';

const PAGE_SIZE = 12;
const ease = [0.22, 1, 0.36, 1];
const STATUS_OPTIONS = ['all', 'queued', 'processing', 'failed', 'done'];
const SORT_OPTIONS = ['updated_desc', 'updated_asc', 'title_asc', 'title_desc', 'reels_desc', 'uploads_desc'];

function toTimestamp(value) {
  const ts = new Date(value || 0).getTime();
  return Number.isNaN(ts) ? 0 : ts;
}

function classifyProjectBucket(project) {
  const status = String(project?.status || '').toUpperCase();
  const uploads = Number(project?.uploadCount || 0);
  const generated = Number(project?.generatedCount || 0);

  if (status.includes('FAILED') || status.includes('ERROR')) return 'failed';
  if (generated > 0 || status.includes('DONE') || status.includes('COMPLETE') || status.includes('SUCCESS')) return 'done';
  if (status.includes('PROCESS') || status.includes('RENDER') || status.includes('ANALY') || uploads > 0) return 'processing';
  return 'queued';
}

function getStatusTone(status) {
  if (status === 'done') return 'border-[#BBF7D0] bg-[#F0FDF4] text-[#166534]';
  if (status === 'failed') return 'border-[#FECACA] bg-[#FEF2F2] text-[#B91C1C]';
  if (status === 'processing') return 'border-[#BFDBFE] bg-[#EFF6FF] text-[#1D4ED8]';
  return 'border-[#E2E8F0] bg-[#F8FAFC] text-[#475569]';
}

function sanitizeSort(sortValue) {
  return SORT_OPTIONS.includes(sortValue) ? sortValue : 'updated_desc';
}

function sanitizeStatus(statusValue) {
  return STATUS_OPTIONS.includes(statusValue) ? statusValue : 'all';
}

function sortProjects(projects, sortBy) {
  const sorted = [...projects];
  sorted.sort((a, b) => {
    if (sortBy === 'updated_asc') return toTimestamp(a.updatedAt) - toTimestamp(b.updatedAt);
    if (sortBy === 'title_asc') return String(a.title || '').localeCompare(String(b.title || ''));
    if (sortBy === 'title_desc') return String(b.title || '').localeCompare(String(a.title || ''));
    if (sortBy === 'reels_desc') return Number(b.generatedCount || 0) - Number(a.generatedCount || 0);
    if (sortBy === 'uploads_desc') return Number(b.uploadCount || 0) - Number(a.uploadCount || 0);
    return toTimestamp(b.updatedAt) - toTimestamp(a.updatedAt);
  });
  return sorted;
}

export default function ProjectsPage() {
  const prefersReducedMotion = useReducedMotion();
  const navigate = useNavigate();
  const toast = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  const [allProjects, setAllProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [statusFilter, setStatusFilter] = useState(sanitizeStatus(searchParams.get('status') || 'all'));
  const [sortBy, setSortBy] = useState(sanitizeSort(searchParams.get('sort') || 'updated_desc'));
  const [page, setPage] = useState(Math.max(1, Number(searchParams.get('page') || 1)));

  useEffect(() => {
    const urlQuery = searchParams.get('q') || '';
    const urlStatus = sanitizeStatus(searchParams.get('status') || 'all');
    const urlSort = sanitizeSort(searchParams.get('sort') || 'updated_desc');
    const pageFromUrl = Math.max(1, Number(searchParams.get('page') || 1));

    if (urlQuery !== query) setQuery(urlQuery);
    if (urlStatus !== statusFilter) setStatusFilter(urlStatus);
    if (urlSort !== sortBy) setSortBy(urlSort);
    if (pageFromUrl !== page) setPage(pageFromUrl);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  useEffect(() => {
    const next = new URLSearchParams();
    const trimmed = query.trim();
    if (trimmed) next.set('q', trimmed);
    if (statusFilter !== 'all') next.set('status', statusFilter);
    if (sortBy !== 'updated_desc') next.set('sort', sortBy);
    if (page > 1) next.set('page', String(page));

    if (next.toString() !== searchParams.toString()) {
      setSearchParams(next, { replace: true });
    }
  }, [page, query, searchParams, setSearchParams, sortBy, statusFilter]);

  const fetchProjects = async () => {
    setLoading(true);
    setError('');
    try {
      const collected = [];
      let currentPage = 1;
      let hasNext = true;

      while (hasNext && currentPage <= 20) {
        const res = await apiFetch(`/projects?page=${currentPage}&limit=100`);
        if (!res.ok) {
          throw new Error('Failed to fetch projects');
        }
        const data = await res.json();
        collected.push(...(data.projects || []));
        hasNext = Boolean(data.has_next);
        currentPage += 1;
      }

      setAllProjects(collected);
    } catch (fetchError) {
      setError('Failed to fetch projects.');
      toast.error('Projects unavailable', 'Could not load projects. Please refresh.');
      console.error(fetchError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const createProject = async () => {
    try {
      const res = await apiFetch('/projects', {
        method: 'POST',
        body: JSON.stringify({ title: 'Untitled Property' }),
      });
      if (res.ok) {
        const project = await res.json();
        toast.success('Project created', 'Opening your new project.');
        navigate(`/dashboard/projects/${project._id}`);
      } else {
        toast.error('Create project failed', 'Please try again.');
      }
    } catch (err) {
      console.error(err);
      toast.error('Create project failed', 'Network or server issue.');
    }
  };

  const filteredProjects = useMemo(() => {
    const trimmed = query.trim().toLowerCase();
    const filtered = allProjects.filter((project) => {
      const bucket = classifyProjectBucket(project);
      if (statusFilter !== 'all' && bucket !== statusFilter) return false;
      if (!trimmed) return true;
      const haystack = `${project.title || ''} ${project.status || ''}`.toLowerCase();
      return haystack.includes(trimmed);
    });
    return sortProjects(filtered, sortBy);
  }, [allProjects, query, sortBy, statusFilter]);

  const pages = Math.max(1, Math.ceil(filteredProjects.length / PAGE_SIZE));
  const hasPrev = page > 1;
  const hasNext = page < pages;

  useEffect(() => {
    if (page > pages) setPage(pages);
  }, [page, pages]);

  const visibleProjects = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filteredProjects.slice(start, start + PAGE_SIZE);
  }, [filteredProjects, page]);

  const signals = useMemo(() => {
    const generated = filteredProjects.reduce((sum, p) => sum + Number(p.generatedCount || 0), 0);
    const uploads = filteredProjects.reduce((sum, p) => sum + Number(p.uploadCount || 0), 0);
    const drafts = filteredProjects.filter((p) => classifyProjectBucket(p) === 'queued').length;

    return [
      { label: 'All Projects', value: allProjects.length },
      { label: 'Current View', value: filteredProjects.length },
      { label: 'Uploads In View', value: uploads },
      { label: 'Drafts In View', value: drafts },
      { label: 'Reels In View', value: generated },
    ];
  }, [allProjects.length, filteredProjects]);

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
              Search quickly, filter by generation state, and sort for review or execution speed.
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
                transition={{ duration: 0.4, ease, delay: prefersReducedMotion ? 0 : 0.08 + index * 0.04 }}
                className="rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-4 py-3.5"
              >
                <p className="font-['Sora'] text-2xl font-extrabold tracking-tight text-[#0F172A]">{signal.value}</p>
                <p className="mt-1 text-[11px] font-extrabold uppercase tracking-[0.08em] text-[#64748B]">{signal.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-semibold text-red-700">
          {error}
        </div>
      ) : null}

      <motion.section
        initial={prefersReducedMotion ? false : { opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease, delay: prefersReducedMotion ? 0 : 0.08 }}
        className="rounded-[1.6rem] border border-[#dbe3f1] bg-white p-6 shadow-[0_20px_45px_rgba(15,23,42,0.06)]"
      >
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-['Sora'] text-xl font-extrabold tracking-tight text-[#0F172A]">Project Grid</h2>
          <span className="rounded-lg border border-[#e2e8f0] bg-[#f8fafc] px-3 py-1.5 text-xs font-extrabold uppercase tracking-[0.08em] text-[#475569]">
            Page {page} of {pages}
          </span>
        </div>

        <div className="mb-5 grid gap-3 lg:grid-cols-[1.4fr_0.8fr_0.8fr]">
          <label className="flex items-center gap-2 rounded-xl border border-[#dbe3f1] bg-[#f8fafc] px-3.5 py-2.5">
            <Search size={15} className="text-[#64748B]" />
            <input
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
              placeholder="Search by project title or status"
              className="w-full bg-transparent text-sm font-medium text-[#0F172A] outline-none placeholder:text-[#94a3b8]"
            />
          </label>

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(sanitizeStatus(e.target.value));
              setPage(1);
            }}
            className="rounded-xl border border-[#dbe3f1] bg-[#f8fafc] px-3.5 py-2.5 text-sm font-semibold text-[#0F172A] outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="queued">Queued</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
            <option value="done">Done</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => {
              setSortBy(sanitizeSort(e.target.value));
              setPage(1);
            }}
            className="rounded-xl border border-[#dbe3f1] bg-[#f8fafc] px-3.5 py-2.5 text-sm font-semibold text-[#0F172A] outline-none"
          >
            <option value="updated_desc">Sort: Recently Updated</option>
            <option value="updated_asc">Sort: Oldest Updated</option>
            <option value="title_asc">Sort: Title A-Z</option>
            <option value="title_desc">Sort: Title Z-A</option>
            <option value="reels_desc">Sort: Most Reels</option>
            <option value="uploads_desc">Sort: Most Uploads</option>
          </select>
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
        ) : allProjects.length === 0 ? (
          <div className="rounded-xl border-2 border-dashed border-[#e2e8f0] bg-[#f8fafc] px-6 py-12 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-white text-[#0284c7] shadow-sm">
              <FolderKanban size={24} />
            </div>
            <p className="text-xl font-extrabold tracking-tight text-[#0F172A]">No projects yet</p>
            <p className="mt-1 text-sm font-medium text-[#64748B]">Create your first project to start building reels.</p>
            <div className="mx-auto mt-4 max-w-lg rounded-xl border border-[#e2e8f0] bg-white px-4 py-3 text-left">
              <p className="text-xs font-extrabold uppercase tracking-[0.08em] text-[#64748B]">Quick Start</p>
              <div className="mt-2 space-y-1.5 text-xs font-semibold text-[#334155]">
                <p>1. Create a project and upload one full home-tour video.</p>
                <p>2. Run AI analysis to generate a clean draft timeline.</p>
                <p>3. Open style/music and render your first final reel.</p>
              </div>
            </div>
            <button
              onClick={createProject}
              className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#0F172A] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#1e293b]"
            >
              <Plus size={16} />
              Create Project
            </button>
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-6 py-10 text-center">
            <p className="text-lg font-extrabold tracking-tight text-[#0F172A]">No matching projects</p>
            <p className="mt-1 text-sm font-medium text-[#64748B]">Try changing search text, status, or sort.</p>
            <button
              type="button"
              onClick={() => {
                setQuery('');
                setStatusFilter('all');
                setSortBy('updated_desc');
                setPage(1);
              }}
              className="mt-4 inline-flex items-center gap-2 rounded-lg border border-[#dbe3f1] bg-white px-4 py-2 text-xs font-bold text-[#0F172A] transition hover:bg-[#eff6ff]"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {visibleProjects.map((project, index) => {
                const bucket = classifyProjectBucket(project);
                return (
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
                            bucket
                          )}`}
                        >
                          {bucket}
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
                );
              })}
            </div>

            <div className="mt-6 flex flex-col items-center justify-between gap-3 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-4 py-3 sm:flex-row">
              <p className="text-sm font-semibold text-[#64748B]">
                Showing {visibleProjects.length} of {filteredProjects.length} filtered projects ({allProjects.length} total).
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
                  onClick={() => setPage((prev) => Math.min(pages, prev + 1))}
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
    </div>
  );
}
