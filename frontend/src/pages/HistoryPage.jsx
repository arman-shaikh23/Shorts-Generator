import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Download, Clock, Film, ChevronLeft, ChevronRight } from 'lucide-react';
import { apiFetch, toApiUrl } from '../api/client';
import { formatRelativeTime } from '../lib/utils';

const PAGE_SIZE = 12;

export default function HistoryPage() {
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

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <div className="relative w-14 h-14">
          <div className="absolute inset-0 border-4 border-[#0EA5E9]/20 rounded-2xl animate-pulse"></div>
          <div className="absolute inset-0 border-4 border-[#0EA5E9] rounded-2xl border-t-transparent animate-spin"></div>
        </div>
        <p className="text-[#64748B] font-bold tracking-wider uppercase text-xs">Loading Reels</p>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="max-w-[1200px] mx-auto">
      <div className="mb-10">
        <h1 className="text-4xl font-black tracking-tight text-[#0F172A] mb-2">Generated Reels</h1>
        <p className="text-lg text-[#64748B] font-medium">Your completed cinematic property tours.</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-100 text-red-600 px-5 py-4 rounded-2xl text-sm font-medium mb-8">
          {error}
        </div>
      )}

      {shorts.length === 0 ? (
        <div className="rounded-[2rem] border-2 border-dashed border-[#E2E8F0] bg-white p-20 flex flex-col items-center justify-center text-center shadow-[0_20px_50px_rgba(0,0,0,0.02)]">
          <div className="w-20 h-20 rounded-full bg-[#F8FAFC] flex items-center justify-center mb-6 border border-[#E2E8F0]">
            <Film size={32} className="text-[#64748B]" />
          </div>
          <h3 className="text-2xl font-black text-[#0F172A] mb-2">No reels generated yet</h3>
          <p className="text-[#64748B] font-medium max-w-sm mb-8">Head over to Projects to start rendering your first video.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {shorts.map((short) => (
              <div key={short._id} className="glass-card rounded-[1.5rem] overflow-hidden hover:shadow-[0_30px_60px_rgba(0,0,0,0.08)] hover:border-[#0EA5E9]/30 transition-all duration-300 group flex flex-col hover:-translate-y-1">
                <div className="aspect-[9/16] bg-[#0F172A] relative flex items-center justify-center overflow-hidden">
                  <video src={toApiUrl(short.videoUrl)} className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-transform duration-700 group-hover:scale-105" controls />
                </div>
                <div className="p-5 flex-1 flex flex-col bg-white">
                  <h3 className="text-base font-black text-[#0F172A] truncate mb-1">{short.projectTitle}</h3>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xs font-bold text-[#0EA5E9] bg-[#0EA5E9]/10 px-2 py-0.5 rounded-md">{short.style}</span>
                    <span className="text-xs font-bold text-[#64748B] bg-[#F8FAFC] border border-[#E2E8F0] px-2 py-0.5 rounded-md">{short.duration}</span>
                  </div>

                  <div className="mb-4">
                    <p className="text-sm font-bold text-[#0F172A] leading-snug line-clamp-2">"{short.hook}"</p>
                    {short.description && (
                      <p className="text-xs font-medium text-[#64748B] mt-1 line-clamp-1">{short.description}</p>
                    )}
                    {short.hashtags && short.hashtags.length > 0 && (
                      <div className="flex gap-1 mt-2 overflow-hidden flex-wrap">
                        {short.hashtags.slice(0, 3).map((tag, i) => (
                          <span key={i} className="text-[10px] font-bold text-[#14B8A6]">{tag}</span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="mt-auto flex items-center justify-between pt-4 border-t border-[#E2E8F0]">
                    <div className="flex items-center text-[10px] font-bold text-[#94a3b8] uppercase tracking-wider gap-1.5">
                      <Clock size={12} />
                      {formatRelativeTime(short.createdAt * 1000)}
                    </div>
                    <button
                      onClick={async () => {
                        const url = toApiUrl(short.videoUrl);
                        try {
                          const response = await fetch(url);
                          const blob = await response.blob();
                          const blobUrl = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = blobUrl;
                          a.download = `${short.projectTitle || 'ReelForge_Video'}.mp4`;
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                          window.URL.revokeObjectURL(blobUrl);
                        } catch (err) {
                          console.error('Download failed', err);
                          window.open(url, '_blank');
                        }
                      }}
                      className="bg-[#F8FAFC] border border-[#E2E8F0] text-[#0F172A] hover:bg-[#0F172A] hover:text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-colors flex items-center gap-1.5"
                    >
                      <Download size={14} /> Save
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 bg-white border border-[#E2E8F0] rounded-2xl px-5 py-4">
            <p className="text-sm font-bold text-[#64748B]">
              Page {page} of {Math.max(1, pages)} - {total} total reels
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                disabled={!hasPrev || loading}
                className="inline-flex items-center gap-1 px-4 py-2 rounded-xl border border-[#E2E8F0] bg-white text-[#0F172A] font-bold text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#F8FAFC]"
              >
                <ChevronLeft size={16} /> Prev
              </button>
              <button
                onClick={() => setPage((prev) => prev + 1)}
                disabled={!hasNext || loading}
                className="inline-flex items-center gap-1 px-4 py-2 rounded-xl border border-[#E2E8F0] bg-white text-[#0F172A] font-bold text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#F8FAFC]"
              >
                Next <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </>
      )}
    </motion.div>
  );
}
