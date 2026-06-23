import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Download,
  Film,
  Search,
  Sparkles,
} from 'lucide-react';
import { apiFetch, toApiUrl } from '../api/client';
import { formatRelativeTime } from '../lib/utils';
import { useToast } from '../context/ToastContext';

const PAGE_SIZE = 12;
const ease = [0.22, 1, 0.36, 1];
const SORT_OPTIONS = ['created_desc', 'created_asc', 'style_asc', 'project_asc'];

function normalizeCreatedAt(value) {
  if (typeof value === 'number') {
    return value < 1_000_000_000_000 ? value * 1000 : value;
  }
  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? Date.now() : parsed;
}

function toTimestamp(value) {
  return normalizeCreatedAt(value);
}

function sanitizeSort(sortValue) {
  return SORT_OPTIONS.includes(sortValue) ? sortValue : 'created_desc';
}

function sortHistory(items, sortBy) {
  const sorted = [...items];
  sorted.sort((a, b) => {
    if (sortBy === 'created_asc') return toTimestamp(a.createdAt) - toTimestamp(b.createdAt);
    if (sortBy === 'style_asc') return String(a.style || '').localeCompare(String(b.style || ''));
    if (sortBy === 'project_asc') return String(a.projectTitle || '').localeCompare(String(b.projectTitle || ''));
    return toTimestamp(b.createdAt) - toTimestamp(a.createdAt);
  });
  return sorted;
}

async function downloadVideo(videoUrl, projectTitle) {
  const url = toApiUrl(videoUrl);
  try {
    const response = await fetch(url);
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = `${projectTitle || 'ReelForge_Video'}.mp4`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(blobUrl);
    return true;
  } catch (err) {
    console.error('Download failed', err);
    window.open(url, '_blank');
    return false;
  }
}

export default function HistoryPage() {
  const prefersReducedMotion = useReducedMotion();
  const toast = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  const [allShorts, setAllShorts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [styleFilter, setStyleFilter] = useState(searchParams.get('style') || 'all');
  const [sortBy, setSortBy] = useState(sanitizeSort(searchParams.get('sort') || 'created_desc'));
  const [page, setPage] = useState(Math.max(1, Number(searchParams.get('page') || 1)));

  useEffect(() => {
    const urlQuery = searchParams.get('q') || '';
    const urlStyle = searchParams.get('style') || 'all';
    const urlSort = sanitizeSort(searchParams.get('sort') || 'created_desc');
    const pageFromUrl = Math.max(1, Number(searchParams.get('page') || 1));

    if (urlQuery !== query) setQuery(urlQuery);
    if (urlStyle !== styleFilter) setStyleFilter(urlStyle);
    if (urlSort !== sortBy) setSortBy(urlSort);
    if (pageFromUrl !== page) setPage(pageFromUrl);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  useEffect(() => {
    const next = new URLSearchParams();
    const trimmed = query.trim();
    if (trimmed) next.set('q', trimmed);
    if (styleFilter !== 'all') next.set('style', styleFilter);
    if (sortBy !== 'created_desc') next.set('sort', sortBy);
    if (page > 1) next.set('page', String(page));

    if (next.toString() !== searchParams.toString()) {
      setSearchParams(next, { replace: true });
    }
  }, [page, query, searchParams, setSearchParams, sortBy, styleFilter]);

  const fetchHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const collected = [];
      let currentPage = 1;
      let hasNext = true;

      while (hasNext && currentPage <= 20) {
        const res = await apiFetch(`/history?page=${currentPage}&limit=100`);
        if (!res.ok) throw new Error('Failed to load history');
        const data = await res.json();
        collected.push(...(data.shorts || []));
        hasNext = Boolean(data.has_next);
        currentPage += 1;
      }

      setAllShorts(collected);
    } catch (fetchError) {
      setError('Failed to load history.');
      toast.error('History unavailable', 'Could not load reels. Please refresh.');
      console.error(fetchError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const styleOptions = useMemo(() => {
    const set = new Set(
      allShorts
        .map((item) => String(item.style || '').trim())
        .filter(Boolean)
        .map((style) => style.toLowerCase())
    );
    return ['all', ...Array.from(set)];
  }, [allShorts]);

  const filteredShorts = useMemo(() => {
    const trimmed = query.trim().toLowerCase();
    const filtered = allShorts.filter((short) => {
      if (styleFilter !== 'all' && String(short.style || '').toLowerCase() !== styleFilter.toLowerCase()) {
        return false;
      }
      if (!trimmed) return true;
      const haystack = `${short.projectTitle || ''} ${short.style || ''} ${short.hook || ''} ${short.description || ''}`.toLowerCase();
      return haystack.includes(trimmed);
    });
    return sortHistory(filtered, sortBy);
  }, [allShorts, query, sortBy, styleFilter]);

  const pages = Math.max(1, Math.ceil(filteredShorts.length / PAGE_SIZE));
  const hasPrev = page > 1;
  const hasNext = page < pages;

  useEffect(() => {
    if (page > pages) setPage(pages);
  }, [page, pages]);

  const visibleShorts = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filteredShorts.slice(start, start + PAGE_SIZE);
  }, [filteredShorts, page]);

  const signals = useMemo(() => {
    const styles = new Set(filteredShorts.map((item) => String(item.style || '').toLowerCase()).filter(Boolean));
    const withHashtags = filteredShorts.filter((item) => Array.isArray(item.hashtags) && item.hashtags.length > 0).length;
    const withDescription = filteredShorts.filter((item) => Boolean(item.description)).length;

    return [
      { label: 'Total Reels', value: allShorts.length },
      { label: 'Current View', value: filteredShorts.length },
      { label: 'Unique Styles', value: styles.size },
      { label: 'With Hashtags', value: withHashtags },
      { label: 'With Description', value: withDescription },
    ];
  }, [allShorts.length, filteredShorts]);

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
              <Film size={14} />
              Export Library
            </span>

            <h1 className="mt-4 font-['Sora'] text-4xl font-extrabold tracking-tight text-[#020617] md:text-5xl">
              Review, replay, and download your completed reels.
            </h1>
            <p className="mt-4 max-w-2xl text-base font-medium leading-relaxed text-[#475569] md:text-lg">
              Search by title or hook, filter by style, and sort for publishing handoff.
            </p>

            <div className="mt-7 flex flex-wrap items-center gap-3">
              <Link
                to="/dashboard/projects"
                className="inline-flex items-center gap-2 rounded-xl border border-[#dbe3f1] bg-white px-5 py-3.5 text-sm font-bold text-[#0F172A] transition hover:border-[#93C5FD] hover:bg-[#F8FAFC]"
              >
                Back To Projects
                <ArrowRight size={16} />
              </Link>
              <button
                type="button"
                onClick={() => {
                  setPage(1);
                  fetchHistory();
                }}
                className="inline-flex items-center gap-2 rounded-xl bg-[#0F172A] px-5 py-3.5 text-sm font-bold text-white transition hover:bg-[#1e293b]"
              >
                <Sparkles size={16} />
                Refresh Library
              </button>
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
          <h2 className="font-['Sora'] text-xl font-extrabold tracking-tight text-[#0F172A]">Rendered Reels</h2>
          <span className="rounded-lg border border-[#e2e8f0] bg-[#f8fafc] px-3 py-1.5 text-xs font-extrabold uppercase tracking-[0.08em] text-[#475569]">
            Page {page} of {pages}
          </span>
        </div>

        <div className="mb-5 grid gap-3 lg:grid-cols-[1.3fr_0.9fr_0.8fr]">
          <label className="flex items-center gap-2 rounded-xl border border-[#dbe3f1] bg-[#f8fafc] px-3.5 py-2.5">
            <Search size={15} className="text-[#64748B]" />
            <input
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
              placeholder="Search by project, hook, description, style"
              className="w-full bg-transparent text-sm font-medium text-[#0F172A] outline-none placeholder:text-[#94a3b8]"
            />
          </label>

          <select
            value={styleFilter}
            onChange={(e) => {
              setStyleFilter(e.target.value);
              setPage(1);
            }}
            className="rounded-xl border border-[#dbe3f1] bg-[#f8fafc] px-3.5 py-2.5 text-sm font-semibold text-[#0F172A] outline-none"
          >
            {styleOptions.map((styleOption) => (
              <option key={styleOption} value={styleOption}>
                {styleOption === 'all' ? 'All Styles' : `Style: ${styleOption}`}
              </option>
            ))}
          </select>

          <select
            value={sortBy}
            onChange={(e) => {
              setSortBy(sanitizeSort(e.target.value));
              setPage(1);
            }}
            className="rounded-xl border border-[#dbe3f1] bg-[#f8fafc] px-3.5 py-2.5 text-sm font-semibold text-[#0F172A] outline-none"
          >
            <option value="created_desc">Sort: Newest</option>
            <option value="created_asc">Sort: Oldest</option>
            <option value="style_asc">Sort: Style A-Z</option>
            <option value="project_asc">Sort: Project A-Z</option>
          </select>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="animate-pulse rounded-2xl border border-[#e2e8f0] bg-[#f8fafc] p-4">
                <div className="aspect-[9/16] rounded-xl bg-[#e2e8f0]" />
                <div className="mt-4 h-4 w-40 rounded bg-[#e2e8f0]" />
                <div className="mt-2 h-3 w-28 rounded bg-[#e2e8f0]" />
              </div>
            ))}
          </div>
        ) : allShorts.length === 0 ? (
          <div className="rounded-xl border-2 border-dashed border-[#e2e8f0] bg-[#f8fafc] px-6 py-12 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-white text-[#0284c7] shadow-sm">
              <Film size={24} />
            </div>
            <p className="text-xl font-extrabold tracking-tight text-[#0F172A]">No reels generated yet</p>
            <p className="mt-1 text-sm font-medium text-[#64748B]">Head to Projects and render your first final reel.</p>
            <div className="mx-auto mt-4 max-w-lg rounded-xl border border-[#e2e8f0] bg-white px-4 py-3 text-left">
              <p className="text-xs font-extrabold uppercase tracking-[0.08em] text-[#64748B]">Before First Export</p>
              <div className="mt-2 space-y-1.5 text-xs font-semibold text-[#334155]">
                <p>1. Upload footage and complete AI analysis.</p>
                <p>2. Finalize storyboard, style, and music settings.</p>
                <p>3. Render final output to populate this reel library.</p>
              </div>
            </div>
            <Link
              to="/dashboard/projects"
              className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#0F172A] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#1e293b]"
            >
              Open Projects
              <ArrowRight size={16} />
            </Link>
          </div>
        ) : filteredShorts.length === 0 ? (
          <div className="rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-6 py-10 text-center">
            <p className="text-lg font-extrabold tracking-tight text-[#0F172A]">No matching reels</p>
            <p className="mt-1 text-sm font-medium text-[#64748B]">Try changing search text, style filter, or sort.</p>
            <button
              type="button"
              onClick={() => {
                setQuery('');
                setStyleFilter('all');
                setSortBy('created_desc');
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
              {visibleShorts.map((short, index) => (
                <motion.article
                  key={short._id}
                  initial={prefersReducedMotion ? false : { opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35, ease, delay: prefersReducedMotion ? 0 : index * 0.03 }}
                  className="group overflow-hidden rounded-2xl border border-[#e2e8f0] bg-[#f8fafc] transition hover:-translate-y-0.5 hover:border-[#bfdbfe] hover:bg-[#eff6ff]"
                >
                  <div className="relative aspect-[9/16] overflow-hidden bg-[#020617]">
                    <video
                      src={toApiUrl(short.videoUrl)}
                      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
                      controls
                      preload="metadata"
                    />
                  </div>

                  <div className="p-4">
                    <div className="mb-3 flex items-start justify-between gap-3">
                      <p className="line-clamp-1 font-['Sora'] text-lg font-extrabold tracking-tight text-[#0F172A]">
                        {short.projectTitle || 'Untitled Reel'}
                      </p>
                      <span className="rounded-md border border-[#dbe3f1] bg-white px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-[0.08em] text-[#475569]">
                        {short.duration || 'Auto'}
                      </span>
                    </div>

                    <div className="mb-3 flex flex-wrap gap-2">
                      <span className="rounded-full border border-[#BFDBFE] bg-[#EFF6FF] px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-[0.08em] text-[#1D4ED8]">
                        {short.style || 'Default'}
                      </span>
                      {Array.isArray(short.hashtags) &&
                        short.hashtags.slice(0, 2).map((tag, tagIndex) => (
                          <span
                            key={`${short._id}-tag-${tagIndex}`}
                            className="rounded-full border border-[#d1fae5] bg-[#f0fdf4] px-2.5 py-1 text-[10px] font-bold text-[#166534]"
                          >
                            {tag}
                          </span>
                        ))}
                    </div>

                    {short.hook ? <p className="line-clamp-2 text-sm font-semibold text-[#334155]">"{short.hook}"</p> : null}
                    {short.description ? (
                      <p className="mt-1 line-clamp-2 text-xs font-medium leading-relaxed text-[#64748B]">{short.description}</p>
                    ) : null}

                    <div className="mt-4 flex items-center justify-between border-t border-[#e2e8f0] pt-3">
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#64748B]">
                        <Clock3 size={13} />
                        {formatRelativeTime(normalizeCreatedAt(short.createdAt))}
                      </span>
                      <button
                        type="button"
                        onClick={async () => {
                          const ok = await downloadVideo(short.videoUrl, short.projectTitle);
                          if (ok) {
                            toast.success('Download started', `${short.projectTitle || 'Reel'} is downloading.`);
                          } else {
                            toast.error('Download fallback', 'Opened video in a new tab due to fetch issue.');
                          }
                        }}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[#dbe3f1] bg-white px-3 py-1.5 text-xs font-bold text-[#0F172A] transition hover:bg-[#0F172A] hover:text-white"
                      >
                        <Download size={13} />
                        Download
                      </button>
                    </div>
                  </div>
                </motion.article>
              ))}
            </div>

            <div className="mt-6 flex flex-col items-center justify-between gap-3 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-4 py-3 sm:flex-row">
              <p className="text-sm font-semibold text-[#64748B]">
                Showing {visibleShorts.length} of {filteredShorts.length} filtered reels ({allShorts.length} total).
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
