import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Download, Clock, Film, Loader2 } from 'lucide-react';
import { apiFetch } from '../api/client';
import { formatRelativeTime } from '../lib/utils';
import { Button } from '../components/ui/Button';

export default function HistoryPage() {
  const [shorts, setShorts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await apiFetch('/history');
      if (res.ok) {
        const data = await res.json();
        setShorts(data.shorts || []);
      } else {
        setError('Failed to load history.');
      }
    } catch {
      setError('Connection error.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="max-w-[1100px]">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-1">Generated Reels</h1>
          <p className="text-gray-500">Your completed cinematic property tours.</p>
        </div>
      </div>

      {error && <div className="text-red-400 bg-red-400/10 p-4 rounded-xl mb-6">{error}</div>}

      {shorts.length === 0 ? (
        <div className="border border-dashed border-white/10 rounded-2xl p-20 flex flex-col items-center justify-center text-gray-500">
          <Film size={40} className="mb-4 opacity-50" />
          <h3 className="text-lg font-medium text-white mb-1">No reels generated yet</h3>
          <p className="text-sm">Head over to Projects to start rendering your first video.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {shorts.map((short) => (
            <div key={short._id} className="bg-[#111] border border-white/10 rounded-2xl overflow-hidden hover:border-white/20 transition group flex flex-col">
              <div className="aspect-[9/16] bg-black relative border-b border-white/10 flex items-center justify-center">
                <video src={`http://localhost:8000${short.videoUrl}`} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition" controls />
              </div>
              <div className="p-5 flex-1 flex flex-col">
                <h3 className="text-base font-bold truncate mb-1">{short.projectTitle}</h3>
                <p className="text-xs text-gray-500 mb-4">{short.style} • {short.duration}</p>
                
                <div className="mt-auto flex items-center justify-between pt-4 border-t border-white/5">
                  <div className="flex items-center text-[11px] text-gray-600 gap-1.5">
                    <Clock size={12} />
                    {formatRelativeTime(short.createdAt)}
                  </div>
                  <a href={`http://localhost:8000${short.videoUrl}`} download>
                    <Button variant="outline" size="sm" className="h-8 text-xs px-3">
                      <Download size={14} className="mr-1" /> Save
                    </Button>
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
