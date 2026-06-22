import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Download,
  Film,
  Sparkles,
} from 'lucide-react';
import { apiFetch, toApiUrl } from '../api/client';
import { formatRelativeTime } from '../lib/utils';

const PAGE_SIZE = 12;
const ease = [0.22, 1, 0.36, 1];

function normalizeCreatedAt(value) {
  if (typeof value === 'number') {
    return value < 1_000_000_000_000 ? value * 1000 : value;
  }
  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? Date.now() : parsed;
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
  } catch (err) {
    console.error('Download failed', err);
    window.open(url, '_blank');
  }
}

export default function HistoryPage() {
  const prefersReducedMotion = useReducedMotion();

  const [shorts, setShorts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);

  const fetchHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiFetch(`/history?page=${page}&limit=${PAGE_SIZE}`);
      if (res.ok) {
        const data = await res.json();
        if ((data.pages || 0) > 0 && page > data.pages) {
          setPage(data.pages);
          return;
        }
        setShorts(data.shorts || []);
        setTotal(data.total || 0);
        setPages(data.pages || 0);
        setHasNext(Boolean(data.has_next));
        setHasPrev(Boolean(data.has_prev));
      } else {
        setError('Failed to load history.');
      }
    } catch {
      setError('Connection error.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      void fetchHistory();
    }, 0);
    return () => clearTimeout(timer);
  }, [page]);

  const signals = useMemo(() => {
    const styles = new Set(
      shorts
        .map((item) => item.style)
        .filter(Boolean)
        .map((style) => String(style).toLowerCase())
    );
    const withHashtags = shorts.filter((item) => Array.isArray(item.hashtags) && item.hashtags.length > 0).length;
    const withDescription = shorts.filter((item) => Boolean(item.description)).length;

    return [
      { label: 'Total Generated', value: total },
      { label: 'Reels On Page', value: shorts.length },
      { label: 'Unique Styles', value: styles.size },
      { label: 'With Hashtags', value: withHashtags },
      { label: 'With Description', value: withDescription },
    ];
  }, [shorts, total]);

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
              This is your final output space for quality checks and publishing handoff across Instagram, TikTok, and Shorts.
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
                onClick={() => setPage(1)}
                className="inline-flex items-center gap-2 rounded-xl bg-[#0F172A] px-5 py-3.5 text-sm font-bold text-white transition hover:bg-[#1e293b]"
              >
                <Sparkles size={16} />
                Refresh First Page
              </button>
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
          <h2 className="font-['Sora'] text-xl font-extrabold tracking-tight text-[#0F172A]">Rendered Reels</h2>
          <span className="rounded-lg border border-[#e2e8f0] bg-[#f8fafc] px-3 py-1.5 text-xs font-extrabold uppercase tracking-[0.08em] text-[#475569]">
            Page {page} of {Math.max(1, pages)}
          </span>
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
        ) : shorts.length === 0 ? (
          <div className="rounded-xl border-2 border-dashed border-[#e2e8f0] bg-[#f8fafc] px-6 py-12 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-white text-[#0284c7] shadow-sm">
              <Film size={24} />
            </div>
            <p className="text-xl font-extrabold tracking-tight text-[#0F172A]">No reels generated yet</p>
            <p className="mt-1 text-sm font-medium text-[#64748B]">Head to Projects and render your first final reel.</p>
            <Link
              to="/dashboard/projects"
              className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#0F172A] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#1e293b]"
            >
              Open Projects
              <ArrowRight size={16} />
            </Link>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {shorts.map((short, index) => (
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

                    {short.hook && <p className="line-clamp-2 text-sm font-semibold text-[#334155]">"{short.hook}"</p>}
                    {short.description && (
                      <p className="mt-1 line-clamp-2 text-xs font-medium leading-relaxed text-[#64748B]">{short.description}</p>
                    )}

                    <div className="mt-4 flex items-center justify-between border-t border-[#e2e8f0] pt-3">
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#64748B]">
                        <Clock3 size={13} />
                        {formatRelativeTime(normalizeCreatedAt(short.createdAt))}
                      </span>
                      <button
                        type="button"
                        onClick={() => downloadVideo(short.videoUrl, short.projectTitle)}
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
                Showing {shorts.length} of {total} reels.
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
          to="/dashboard/history"
          className="rounded-xl border border-[#bfdbfe] bg-[#eff6ff] px-4 py-3 transition hover:bg-[#dbeafe]"
        >
          <p className="text-sm font-extrabold text-[#0F172A]">Current Library</p>
          <p className="mt-0.5 text-xs font-semibold text-[#0369a1]">Final outputs and approval flow</p>
        </Link>
        <Link
          to="/dashboard/projects"
          className="rounded-xl border border-[#d1fae5] bg-[#f0fdf4] px-4 py-3 transition hover:bg-[#dcfce7]"
        >
          <p className="text-sm font-extrabold text-[#0F172A]">Need New Reel?</p>
          <p className="mt-0.5 text-xs font-semibold text-[#166534]">Return to projects and render more</p>
        </Link>
        <Link
          to="/dashboard"
          className="rounded-xl border border-[#fde68a] bg-[#fffbeb] px-4 py-3 transition hover:bg-[#fef3c7]"
        >
          <p className="text-sm font-extrabold text-[#0F172A]">Dashboard Summary</p>
          <p className="mt-0.5 text-xs font-semibold text-[#92400e]">Back to workspace metrics</p>
        </Link>
      </motion.section>
    </div>
  );
}
