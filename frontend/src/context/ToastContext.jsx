import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

const toastStyle = {
  success: {
    icon: CheckCircle2,
    tone: 'border-[#BBF7D0] bg-[#F0FDF4] text-[#166534]',
  },
  error: {
    icon: AlertCircle,
    tone: 'border-[#FECACA] bg-[#FEF2F2] text-[#B91C1C]',
  },
  info: {
    icon: Info,
    tone: 'border-[#BFDBFE] bg-[#EFF6FF] text-[#1D4ED8]',
  },
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const idCounter = useRef(0);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    ({ type = 'info', title, message = '', duration = 3200 }) => {
      const id = ++idCounter.current;
      const normalizedType = toastStyle[type] ? type : 'info';
      const toast = { id, type: normalizedType, title, message };
      setToasts((prev) => [...prev, toast].slice(-4));

      window.setTimeout(() => {
        removeToast(id);
      }, duration);
      return id;
    },
    [removeToast]
  );

  const api = useMemo(
    () => ({
      addToast,
      success: (title, message, duration) => addToast({ type: 'success', title, message, duration }),
      error: (title, message, duration) => addToast({ type: 'error', title, message, duration }),
      info: (title, message, duration) => addToast({ type: 'info', title, message, duration }),
      removeToast,
    }),
    [addToast, removeToast]
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-[100] flex w-[min(92vw,380px)] flex-col gap-2">
        <AnimatePresence>
          {toasts.map((toast) => {
            const style = toastStyle[toast.type] || toastStyle.info;
            const Icon = style.icon;
            return (
              <motion.article
                key={toast.id}
                initial={{ opacity: 0, y: -8, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.98 }}
                transition={{ duration: 0.2 }}
                className={`pointer-events-auto rounded-xl border px-3.5 py-3 shadow-[0_12px_28px_rgba(15,23,42,0.12)] ${style.tone}`}
              >
                <div className="flex items-start gap-2">
                  <Icon size={16} className="mt-0.5 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-extrabold leading-tight">{toast.title}</p>
                    {toast.message ? <p className="mt-0.5 text-xs font-semibold opacity-90">{toast.message}</p> : null}
                  </div>
                  <button
                    type="button"
                    onClick={() => removeToast(toast.id)}
                    className="rounded-md p-0.5 opacity-80 transition hover:opacity-100"
                    aria-label="Dismiss toast"
                  >
                    <X size={14} />
                  </button>
                </div>
              </motion.article>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return ctx;
}
