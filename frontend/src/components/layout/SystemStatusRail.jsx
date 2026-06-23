import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { apiFetch } from '../../api/client';
import { formatRelativeTime } from '../../lib/utils';

const statusMeta = {
  queued: {
    label: 'Queued',
    icon: Clock3,
    tone: 'border-[#E2E8F0] bg-[#F8FAFC] text-[#475569]',
    accent: 'text-[#64748B]',
  },
  processing: {
    label: 'Processing',
    icon: Loader2,
    tone: 'border-[#BFDBFE] bg-[#EFF6FF] text-[#1D4ED8]',
    accent: 'text-[#0369A1]',
  },
  failed: {
    label: 'Failed',
    icon: AlertTriangle,
    tone: 'border-[#FECACA] bg-[#FEF2F2] text-[#B91C1C]',
    accent: 'text-[#B91C1C]',
  },
  done: {
    label: 'Done',
    icon: CheckCircle2,
    tone: 'border-[#BBF7D0] bg-[#F0FDF4] text-[#166534]',
    accent: 'text-[#15803D]',
  },
};

function toTimestamp(value) {
  const ts = new Date(value || 0).getTime();
  return Number.isNaN(ts) ? 0 : ts;
}

function classifyProject(project) {
  const status = String(project?.status || '').toUpperCase();
  const uploads = Number(project?.uploadCount || 0);
  const generated = Number(project?.generatedCount || 0);

  if (status.includes('FAILED') || status.includes('ERROR')) return 'failed';
  if (generated > 0 || status.includes('DONE') || status.includes('COMPLETE') || status.includes('SUCCESS')) return 'done';
  if (status.includes('PROCESS') || status.includes('RENDER') || status.includes('ANALY') || uploads > 0) return 'processing';
  return 'queued';
}

export function SystemStatusRail() {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [snapshot, setSnapshot] = useState({
    queued: { count: 0, latest: null },
    processing: { count: 0, latest: null },
    failed: { count: 0, latest: null },
    done: { count: 0, latest: null },
  });

  const hydrateStatus = async (quiet = false) => {
    if (!quiet) setLoading(true);
    setIsRefreshing(quiet);
    setError('');
    try {
      const res = await apiFetch('/projects?page=1&limit=30');
      if (!res.ok) {
        setError('Status unavailable');
        return;
      }
      const data = await res.json();
      const projects = data.projects || [];

      const next = {
        queued: { count: 0, latest: null },
        processing: { count: 0, latest: null },
        failed: { count: 0, latest: null },
        done: { count: 0, latest: null },
      };

      projects.forEach((project) => {
        const bucket = classifyProject(project);
        next[bucket].count += 1;
        if (!next[bucket].latest || toTimestamp(project.updatedAt) > toTimestamp(next[bucket].latest.updatedAt)) {
          next[bucket].latest = project;
        }
      });

      setSnapshot(next);
    } catch {
      setError('Status unavailable');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    hydrateStatus();
    const timer = setInterval(() => {
      hydrateStatus(true);
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  const action = useMemo(() => {
    if (snapshot.failed.count > 0 && snapshot.failed.latest?._id) {
      return {
        label: 'Retry Failed',
        onClick: () => navigate(`/dashboard/projects/${snapshot.failed.latest._id}`),
      };
    }
    if (snapshot.processing.count > 0 && snapshot.processing.latest?._id) {
      return {
        label: 'Resume Processing',
        onClick: () => navigate(`/dashboard/projects/${snapshot.processing.latest._id}`),
      };
    }
    if (snapshot.queued.count > 0 && snapshot.queued.latest?._id) {
      return {
        label: 'Continue Setup',
        onClick: () => navigate(`/dashboard/projects/${snapshot.queued.latest._id}`),
      };
    }
    return {
      label: 'Open History',
      onClick: () => navigate('/dashboard/history'),
    };
  }, [navigate, snapshot]);

  return (
    <section className="mb-5 rounded-2xl border border-[#dbe3f1] bg-white px-4 py-3 shadow-[0_12px_30px_rgba(15,23,42,0.05)] md:px-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-[#BFDBFE] bg-[#EFF6FF] px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-[0.08em] text-[#0369A1]">
            System Status
          </span>
          {error ? <p className="text-xs font-semibold text-[#b91c1c]">{error}</p> : null}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => hydrateStatus(true)}
            className="inline-flex items-center gap-1 rounded-lg border border-[#dbe3f1] bg-[#f8fafc] px-2.5 py-1.5 text-[11px] font-bold text-[#334155] transition hover:bg-[#eff6ff]"
          >
            <RefreshCw size={12} className={isRefreshing ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            type="button"
            onClick={action.onClick}
            className="inline-flex items-center gap-1.5 rounded-lg bg-[#0F172A] px-3 py-1.5 text-[11px] font-extrabold uppercase tracking-[0.08em] text-white transition hover:bg-[#1e293b]"
          >
            {action.label}
            <ArrowRight size={12} />
          </button>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 xl:grid-cols-4">
        {Object.entries(statusMeta).map(([key, meta]) => {
          const item = snapshot[key];
          const Icon = meta.icon;
          const latestUpdated = item.latest?.updatedAt ? formatRelativeTime(item.latest.updatedAt) : 'No activity';
          const isInteractive = !loading && item.count > 0;
          const handleDrillDown = () => {
            if (!isInteractive) return;
            if (key === 'done') {
              navigate('/dashboard/history');
              return;
            }
            navigate(`/dashboard/projects?status=${key}&page=1`);
          };
          return (
            <button
              key={key}
              type="button"
              onClick={handleDrillDown}
              className={`rounded-xl border px-3 py-2.5 text-left transition ${meta.tone} ${
                isInteractive ? 'cursor-pointer hover:-translate-y-[1px]' : 'cursor-default opacity-90'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Icon size={13} className={key === 'processing' && item.count > 0 ? 'animate-spin' : ''} />
                  <p className="text-[11px] font-extrabold uppercase tracking-[0.08em]">{meta.label}</p>
                </div>
                <p className="font-['Sora'] text-lg font-extrabold leading-none">{loading ? '--' : item.count}</p>
              </div>
              <p className={`mt-1 text-[11px] font-semibold ${meta.accent}`}>
                {item.count > 0 ? `Latest ${latestUpdated}` : latestUpdated}
              </p>
            </button>
          );
        })}
      </div>

      {location.pathname === '/dashboard' ? null : (
        <p className="mt-2 text-[11px] font-medium text-[#64748B]">
          Status rail is persistent across dashboard pages for quick monitoring.
        </p>
      )}
    </section>
  );
}
