import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { X, Volume2, VolumeX, Play } from 'lucide-react';

export default function HowItWorksModal({ 
  isOpen, 
  onClose, 
  videoUrl = "/tutorials/how-it-works.mp4", 
  title = "How ReelForge Works", 
  description = "Learn how to upload property videos, generate AI reels, add captions, and export the final cinematic video." 
}) {
  const modalRef = useRef(null);
  const videoRef = useRef(null);
  const closeBtnRef = useRef(null);
  const [isMuted, setIsMuted] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }

      if (e.key !== 'Tab' || !modalRef.current) return;

      const focusable = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (!focusable.length) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
      const focusTimer = window.setTimeout(() => closeBtnRef.current?.focus(), 0);

      return () => {
        window.clearTimeout(focusTimer);
        document.removeEventListener('keydown', handleKeyDown);
        document.body.style.overflow = 'unset';
      };
    }
    return undefined;
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    if (modalRef.current && !modalRef.current.contains(e.target)) {
      onClose();
    }
  };

  return createPortal(
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm transition-opacity"
      onClick={handleBackdropClick}
    >
      <div 
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="how-it-works-title"
        aria-describedby="how-it-works-description"
        tabIndex={-1}
        className="relative w-full max-w-4xl max-h-[90vh] bg-white dark:bg-[#0F172A] rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-800">
          <h2 id="how-it-works-title" className="text-xl font-semibold text-gray-900 dark:text-white">
            {title}
          </h2>
          <button 
            ref={closeBtnRef}
            type="button"
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Description / Content */}
        <div className="px-5 py-3 flex-shrink-0 bg-gray-50/50 dark:bg-gray-800/30">
          <p id="how-it-works-description" className="text-gray-600 dark:text-gray-300 text-xs md:text-sm leading-snug">
            {description}
          </p>
          <div className="mt-2.5 grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] md:text-xs font-medium text-gray-700 dark:text-gray-300">
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500"></div>
              Upload Videos
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-purple-500"></div>
              Generate AI Reel
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-pink-500"></div>
              Add Captions
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
              Export Final
            </div>
          </div>
        </div>

        {/* Video Container */}
        <div className="relative w-full bg-black aspect-video flex-shrink-0 group/video cursor-pointer" onClick={togglePlay}>
          <video 
            ref={videoRef}
            className="w-full h-full object-contain"
            src={videoUrl}
            muted={isMuted}
            loop
            playsInline
            controlsList="nodownload noplaybackrate noremoteplayback"
            disablePictureInPicture
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onTimeUpdate={() => setCurrentTime(videoRef.current?.currentTime || 0)}
            onLoadedMetadata={() => setDuration(videoRef.current?.duration || 0)}
          >
            Your browser does not support the video tag.
          </video>
          
          {/* Custom Play/Pause Overlay */}
          {!isPlaying && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/30 transition-opacity">
              <div className="w-16 h-16 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center text-white hover:bg-white/30 transition-colors shadow-2xl">
                <Play size={32} className="ml-1" />
              </div>
            </div>
          )}

          {/* Custom Audio Toggle */}
          <button 
            type="button"
            onClick={(e) => { e.stopPropagation(); setIsMuted(!isMuted); }}
            className="absolute top-4 right-4 p-2.5 bg-black/60 hover:bg-black/80 backdrop-blur-md text-white rounded-full transition-colors shadow-lg z-20"
            aria-label={isMuted ? "Unmute video" : "Mute video"}
          >
            {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
          </button>

          {/* Progress Bar Overlay */}
          <div 
            className="absolute bottom-0 left-0 right-0 px-3 pb-3 pt-4 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover/video:opacity-100 transition-opacity z-20 flex items-center gap-3"
            onClick={(e) => e.stopPropagation()}
          >
            <span className="text-white text-xs font-medium font-mono drop-shadow-md">
              {Math.floor(currentTime / 60)}:{(Math.floor(currentTime % 60)).toString().padStart(2, '0')}
            </span>
            <input
              type="range"
              min="0"
              max={duration || 100}
              step="0.01"
              value={currentTime}
              onChange={(e) => {
                const newTime = parseFloat(e.target.value);
                setCurrentTime(newTime);
                if (videoRef.current) {
                  videoRef.current.currentTime = newTime;
                }
              }}
              className="flex-1 h-1.5 bg-gray-500/50 rounded-lg appearance-none cursor-pointer accent-blue-500 hover:h-2 transition-all"
            />
            <span className="text-white text-xs font-medium font-mono drop-shadow-md">
              {Math.floor(duration / 60)}:{(Math.floor(duration % 60)).toString().padStart(2, '0')}
            </span>
          </div>
        </div>


      </div>
    </div>,
    document.body
  );
}
