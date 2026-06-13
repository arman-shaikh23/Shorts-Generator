import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, GripVertical, Download, X, Link2, Plus, Loader2, Play, Sparkles, CheckCircle2, Film, Activity, Video } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { ProgressStepper } from '../components/ui/ProgressStepper';
import { useSSE } from '../hooks/useSSE';
import { apiFetch, getAccessToken } from '../api/client';

export default function ProjectDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  // --- State ---
  const [loading, setLoading] = useState(!!id);
  const [project, setProject] = useState(null);
  const [uploads, setUploads] = useState([]);
  
  const [uploadMode, setUploadMode] = useState('links');
  const [urlInput, setUrlInput] = useState('');
  const [draggedIdx, setDraggedIdx] = useState(null);
  const horizontalScrollRef = useRef(null);

  const [reelDuration, setReelDuration] = useState('30 sec');
  const [reelStyle, setReelStyle] = useState('Luxury');
  const [exportQuality, setExportQuality] = useState('1080p');

  const { isProcessing, steps, currentStep, result, error, start } = useSSE();
  const [localError, setLocalError] = useState('');

  // --- Fetch Data ---
  const fetchProjectData = useCallback(async (isPolling = false) => {
    if (!id) return;
    try {
      const [projRes, upRes] = await Promise.all([
        apiFetch(`/projects/${id}`),
        apiFetch(`/projects/${id}/uploads`),
      ]);
      if (projRes.ok && upRes.ok) {
        const projData = await projRes.json();
        const upData = await upRes.json();
        setProject(projData);
        setUploads(upData.uploads || []);
      } else if (!isPolling) {
        setLocalError('Failed to load project details.');
      }
    } catch {
      if (!isPolling) setLocalError('Connection error.');
    } finally {
      if (!isPolling) setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchProjectData();
    const interval = setInterval(() => {
      fetchProjectData(true);
    }, 10000);
    return () => clearInterval(interval);
  }, [fetchProjectData]);

  // --- Project Actions ---
  const handleTitleBlur = async (e) => {
    const newTitle = e.target.value;
    if (newTitle !== project.title) {
      setProject({ ...project, title: newTitle });
      await apiFetch(`/projects/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ title: newTitle }),
      });
    }
  };

  // --- Upload Actions ---
  const addUrl = async () => {
    const val = urlInput.trim();
    if (!val) return;
    setUrlInput('');
    try {
      await apiFetch(`/projects/${id}/uploads`, {
        method: 'POST',
        body: JSON.stringify({ urls: [val] }),
      });
      fetchProjectData();
    } catch {
      setLocalError('Failed to add URL.');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); addUrl(); }
  };

  const removeClip = async (uploadId) => {
    setUploads((prev) => prev.filter((u) => u._id !== uploadId));
    try {
      await apiFetch(`/projects/${id}/uploads/${uploadId}`, { method: 'DELETE' });
    } catch {
      fetchProjectData();
    }
  };

  const handleLocalUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        await apiFetch(`/projects/${id}/uploads/file`, {
          method: 'POST',
          body: formData
        });
      } catch (err) {
        setLocalError(`Failed to upload ${file.name}`);
      }
    }
    fetchProjectData();
    e.target.value = null;
  };

  // --- Drag & Drop ---
  const handleDragStart = (idx) => setDraggedIdx(idx);
  const handleDragOver = (e) => e.preventDefault();
  const handleDrop = async (idx) => {
    if (draggedIdx === null || draggedIdx === idx) return;
    
    const items = [...uploads];
    const [moved] = items.splice(draggedIdx, 1);
    items.splice(idx, 0, moved);
    setUploads(items);
    setDraggedIdx(null);

    const orderedIds = items.map((u) => u._id);
    try {
      await apiFetch(`/projects/${id}/uploads/reorder`, {
        method: 'PATCH',
        body: JSON.stringify({ upload_ids: orderedIds }),
      });
    } catch {
      fetchProjectData();
    }
  };

  // --- Analyze & Generate ---
  const handleAnalyze = () => {
    if (!project?.title?.trim()) {
      setLocalError('Enter a property name.'); return;
    }
    const readyClips = uploads.filter(u => u.status === 'PROCESSED');
    if (readyClips.length < 3) {
      setLocalError(`Add at least 3 clips. Currently ${readyClips.length} ready.`); return;
    }
    setLocalError('');
    const params = new URLSearchParams();
    params.append('duration', reelDuration);
    params.append('style', reelStyle);
    const token = getAccessToken() || '';
    start(`http://localhost:8000/api/v1/projects/${id}/generation/analyze?${params.toString()}&token=${token}`);
  };

  const handleGenerateReel = () => {
    const params = new URLSearchParams();
    params.append('duration', reelDuration);
    params.append('style', reelStyle);
    const token = getAccessToken() || '';
    start(`http://localhost:8000/api/v1/projects/${id}/generation/generate?${params.toString()}&token=${token}`);
  };

  // --- Helpers ---
  if (loading) {
    return (
      <div className="flex justify-center items-center h-full">
        <Loader2 className="w-8 h-8 text-[#8B5CF6] animate-spin" />
      </div>
    );
  }

  const displayError = localError || error;
  const resultsData = result?.results || [];
  const readyClips = uploads.filter(u => u.status === 'PROCESSED');
  const hasUploads = uploads.length > 0;

  // Mock AI Director Data based on uploads
  const detectedScenes = [
    { name: 'Exterior', detected: readyClips.length > 0 },
    { name: 'Living Room', detected: readyClips.length > 2 },
    { name: 'Kitchen', detected: readyClips.length > 4 },
    { name: 'Bedroom', detected: readyClips.length > 5 },
    { name: 'Drone Footage', detected: readyClips.length > 7 },
  ];

  const getMediaUrl = (item) => {
    if (item.previewPath) return `http://localhost:8000/${item.previewPath.replace(/\\/g, '/')}`;
    if (item.originalUrl?.startsWith('http')) return item.originalUrl;
    return null;
  };

  return (
    <div className="flex gap-6 h-full max-w-[1600px] mx-auto">
      
      {/* ──── LEFT WORKSPACE ──── */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-y-auto pr-2 custom-scrollbar">
        
        {/* Workspace Header - Top Bar */}
        <div className="glass-card rounded-2xl p-5 mb-6 sticky top-0 z-10">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1 block">Property Name</label>
              <input
                type="text"
                defaultValue={project?.title || ''}
                onBlur={handleTitleBlur}
                placeholder="Name your property..."
                className="w-full bg-transparent text-xl font-bold text-white placeholder:text-gray-600 focus:outline-none"
              />
            </div>
            
            <div className="flex items-center gap-4">
              <div className="bg-black/30 rounded-xl px-4 py-2 border border-white/5">
                <label className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1 block">Style</label>
                <select value={reelStyle} onChange={(e) => setReelStyle(e.target.value)} className="bg-transparent text-sm font-medium text-white focus:outline-none cursor-pointer">
                  <option value="Luxury">Luxury</option>
                  <option value="Cinematic">Cinematic</option>
                  <option value="Viral">Instagram Viral</option>
                  <option value="Realtor">Realtor Style</option>
                </select>
              </div>

              <div className="bg-black/30 rounded-xl px-4 py-2 border border-white/5">
                <label className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1 block">Duration</label>
                <select value={reelDuration} onChange={(e) => setReelDuration(e.target.value)} className="bg-transparent text-sm font-medium text-white focus:outline-none cursor-pointer">
                  <option value="20 sec">20s (Reel)</option>
                  <option value="30 sec">30s (TikTok)</option>
                  <option value="45 sec">45s (Shorts)</option>
                </select>
              </div>

              <div className="bg-black/30 rounded-xl px-4 py-2 border border-white/5">
                <label className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1 block">Quality</label>
                <select value={exportQuality} onChange={(e) => setExportQuality(e.target.value)} className="bg-transparent text-sm font-medium text-white focus:outline-none cursor-pointer">
                  <option value="1080p">1080p HD</option>
                  <option value="4k">4K Ultra HD</option>
                </select>
              </div>

              <div className="bg-black/30 rounded-xl px-4 py-2 border border-white/5 flex flex-col justify-center">
                <label className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1 block">Clips</label>
                <div className="text-sm font-bold text-[#8B5CF6]">{uploads.length} / 15</div>
              </div>
            </div>
          </div>
        </div>

        {displayError && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-300 px-5 py-3 rounded-xl text-sm mb-6 flex items-center justify-between">
            <span>{displayError}</span>
            <button onClick={() => setLocalError('')} className="text-red-400 hover:text-red-300"><X size={16} /></button>
          </div>
        )}

        {/* Upload Section - Collapses slightly if there are uploads */}
        <div className={`transition-all duration-500 mb-6 ${hasUploads ? 'opacity-80 hover:opacity-100' : ''}`}>
          <div className="glass-card rounded-2xl overflow-hidden">
            <div className="flex border-b border-white/5">
              {[
                { id: 'links', label: 'Drop URL', icon: Link2 },
                { id: 'dropbox', label: 'Dropbox', icon: UploadCloud },
                { id: 'upload', label: 'Local Files', icon: Video },
              ].map((tab) => (
                <button 
                  key={tab.id} 
                  onClick={() => setUploadMode(tab.id)} 
                  className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition ${uploadMode === tab.id ? 'bg-white/5 text-white border-b-2 border-[#8B5CF6]' : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.02]'}`}
                >
                  <tab.icon size={16} />{tab.label}
                </button>
              ))}
            </div>
            
            <div className="p-5 bg-black/20">
              {uploadMode === 'links' && (
                <div className="flex gap-3">
                  <input type="text" value={urlInput} onChange={(e) => setUrlInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Paste a video URL..." className="flex-1 bg-black/40 border border-[#22252A] rounded-xl px-4 py-3 text-white placeholder:text-gray-600 text-sm focus:outline-none focus:border-[#6366F1]/50 transition" />
                  <button onClick={addUrl} className="bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white px-6 rounded-xl font-medium flex items-center gap-2 hover:opacity-90 transition"><Plus size={18} /> Import</button>
                </div>
              )}
              {uploadMode === 'dropbox' && (
                <div className="flex gap-3">
                  <input type="text" value={urlInput} onChange={(e) => setUrlInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Paste a Dropbox folder URL..." className="flex-1 bg-black/40 border border-[#22252A] rounded-xl px-4 py-3 text-white placeholder:text-gray-600 text-sm focus:outline-none focus:border-[#6366F1]/50 transition" />
                  <button onClick={addUrl} className="bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white px-6 rounded-xl font-medium flex items-center gap-2 hover:opacity-90 transition"><Plus size={18} /> Sync</button>
                </div>
              )}
              {uploadMode === 'upload' && (
                <div className="flex flex-col items-center justify-center py-8 border border-dashed border-[#22252A] rounded-xl bg-black/40 hover:bg-black/60 transition cursor-pointer" onClick={() => document.getElementById('local-file-upload').click()}>
                  <UploadCloud size={32} className="text-[#8B5CF6] mb-3" />
                  <p className="text-sm font-medium text-white mb-1">Drag & drop or click to browse</p>
                  <p className="text-xs text-gray-500">Supports MP4, MOV up to 4K</p>
                  <input type="file" id="local-file-upload" className="hidden" multiple accept="video/mp4,video/quicktime" onChange={handleLocalUpload} />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* AI Director Panel */}
        {hasUploads && (
          <div className="glass-card rounded-2xl p-5 mb-6 flex gap-6 items-center">
            <div className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#10B981]/20 to-[#10B981]/10 border border-[#10B981]/20">
              <Activity size={24} className="text-[#10B981]" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-bold text-white mb-1 flex items-center gap-2">AI Scene Detection <span className="text-[10px] bg-[#10B981]/20 text-[#10B981] px-2 py-0.5 rounded-full uppercase tracking-wider font-bold">Active</span></h3>
              <p className="text-xs text-gray-400 mb-3">Analyzing raw footage to build property context.</p>
              
              <div className="flex flex-wrap gap-3">
                {detectedScenes.map((scene, i) => (
                  <div key={i} className={`flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1 rounded-lg border ${scene.detected ? 'bg-[#10B981]/10 border-[#10B981]/20 text-[#10B981]' : 'bg-white/5 border-white/5 text-gray-500'}`}>
                    <CheckCircle2 size={12} className={scene.detected ? "text-[#10B981]" : "text-gray-600"} />
                    {scene.name}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Horizontal Story Builder */}
        <div className="glass-card rounded-2xl p-5 mb-8">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Film size={18} className="text-[#8B5CF6]" /> 
                Story Timeline
              </h2>
              <p className="text-xs text-gray-400 mt-1">Drag to reorder clips. AI will use this pool to build the reel.</p>
            </div>
            
            {project?.draftTimeline ? (
              <button onClick={handleGenerateReel} disabled={isProcessing} className="bg-gradient-to-r from-[#10B981] to-teal-500 text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-lg shadow-[#10B981]/20 hover:scale-105 transition active:scale-95 disabled:opacity-50 disabled:pointer-events-none flex items-center gap-2">
                {isProcessing ? <><Loader2 size={16} className="animate-spin" /> Rendering</> : <><Play size={16} fill="white" /> Generate Reel</>}
              </button>
            ) : (
              <button onClick={handleAnalyze} disabled={isProcessing || readyClips.length < 3} className="bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-lg shadow-[#6366F1]/20 hover:scale-105 transition active:scale-95 disabled:opacity-50 disabled:pointer-events-none flex items-center gap-2">
                {isProcessing ? <><Loader2 size={16} className="animate-spin" /> Analyzing</> : <><Sparkles size={16} /> Analyze Story</>}
              </button>
            )}
          </div>

          {!hasUploads ? (
            <div className="h-48 border border-dashed border-[#22252A] rounded-xl bg-black/20 flex flex-col items-center justify-center text-gray-500">
              <Film size={32} className="mb-3 opacity-50" />
              <p className="text-sm font-medium">Your timeline is empty</p>
              <p className="text-xs mt-1 opacity-70">Upload videos above to populate the timeline</p>
            </div>
          ) : (
            <div 
              ref={horizontalScrollRef}
              className="flex gap-4 overflow-x-auto pb-4 pt-2 px-1 snap-x custom-scrollbar"
              style={{ scrollBehavior: 'smooth' }}
            >
              <AnimatePresence>
                {uploads.map((item, idx) => {
                  const mediaUrl = getMediaUrl(item);
                  return (
                    <motion.div 
                      key={item._id} 
                      layout 
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      draggable 
                      onDragStart={() => handleDragStart(idx)} 
                      onDragOver={handleDragOver} 
                      onDrop={() => handleDrop(idx)} 
                      className="group relative flex-shrink-0 w-44 rounded-xl border border-[#22252A] bg-[#0c0c10] overflow-hidden cursor-grab active:cursor-grabbing snap-start hover:border-[#6366F1]/50 hover:shadow-lg hover:shadow-[#6366F1]/10 transition-all"
                    >
                      {/* Thumbnail Area */}
                      <div className="relative h-56 bg-black flex items-center justify-center overflow-hidden">
                        {mediaUrl ? (
                          <video src={mediaUrl} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition duration-300" />
                        ) : (
                          <div className="text-[#22252A]"><Video size={48} /></div>
                        )}
                        
                        {/* Status Overlay */}
                        <div className="absolute top-2 left-2 right-2 flex justify-between">
                          <div className="backdrop-blur-md bg-black/40 border border-white/10 rounded-lg px-2 py-1 text-[10px] font-bold text-white flex items-center gap-1">
                            {idx + 1}
                          </div>
                          {item.status === 'PENDING' && <div className="backdrop-blur-md bg-black/40 border border-white/10 rounded-lg px-2 py-1 text-[10px] font-bold text-gray-300">Wait</div>}
                          {item.status === 'PROCESSING' && <div className="backdrop-blur-md bg-blue-500/20 border border-blue-500/30 rounded-lg px-2 py-1 text-[10px] font-bold text-blue-300 flex items-center gap-1"><Loader2 size={10} className="animate-spin" /></div>}
                        </div>

                        {/* AI Score (Mocked if missing) */}
                        {item.status === 'PROCESSED' && (
                          <div className="absolute bottom-2 right-2 backdrop-blur-md bg-[#10B981]/20 border border-[#10B981]/30 rounded-lg px-2 py-1 text-[10px] font-bold text-[#10B981] flex items-center gap-1">
                            AI {(Math.random() * (98 - 85) + 85).toFixed(0)}
                          </div>
                        )}
                        
                        {/* Remove Button */}
                        <button onClick={() => removeClip(item._id)} className="absolute top-2 right-2 w-6 h-6 backdrop-blur-md bg-black/50 border border-white/10 rounded-md flex items-center justify-center text-gray-400 hover:text-red-400 hover:bg-red-500/20 transition opacity-0 group-hover:opacity-100">
                          <X size={12} />
                        </button>
                      </div>

                      {/* Card Meta */}
                      <div className="p-3 border-t border-[#22252A]">
                        <p className="text-xs font-semibold text-white truncate" title={item.filename}>{item.filename}</p>
                        <div className="flex items-center gap-2 mt-1.5 text-[10px] font-medium text-gray-500">
                          <span className="bg-white/5 px-1.5 py-0.5 rounded text-gray-400">{project?.draftTimeline ? project.draftTimeline[idx]?.scene_type || 'Clip' : 'Raw Clip'}</span>
                          <span>•</span>
                          <span>{item.duration || '0:05'}</span>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

      {/* ──── RIGHT STICKY PREVIEW PANEL ──── */}
      <div className="w-[420px] shrink-0 flex flex-col gap-6">
        <div className="sticky top-0 pt-0 pb-6 flex flex-col gap-6 h-full overflow-y-auto custom-scrollbar">
          
          {/* Main Sticky Video Preview */}
          <div className="glass-card rounded-2xl overflow-hidden flex flex-col shadow-2xl">
            <div className="bg-[#050508] border-b border-[#22252A] p-4 flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-white">
                <Play size={14} className="text-[#8B5CF6]" fill="currentColor" />
                Preview Studio
              </div>
              <div className="flex gap-1">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500/50"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-green-500/50"></div>
              </div>
            </div>
            
            <div className="bg-black aspect-[9/16] relative flex items-center justify-center overflow-hidden">
              {resultsData.length > 0 ? (
                <video src={`http://localhost:8000${resultsData[0].video_url || resultsData[0].videoUrl || ''}`} controls className="w-full h-full object-contain" autoPlay loop muted />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-600 bg-gradient-to-b from-transparent to-[#0a0a0f]/50">
                  {isProcessing ? (
                    <>
                      <Loader2 size={48} className="animate-spin text-[#8B5CF6] mb-4" />
                      <p className="text-sm font-medium text-[#8B5CF6]">AI is rendering...</p>
                    </>
                  ) : (
                    <>
                      <Play size={48} className="opacity-20 mb-4" />
                      <p className="text-sm font-medium text-gray-500">Preview will appear here</p>
                    </>
                  )}
                </div>
              )}
            </div>
            
            {/* AI Asset Settings below player */}
            <div className="p-5 bg-gradient-to-b from-[#111827] to-[#0A0A0B]">
              <div className="mb-4">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Generated Captions</h4>
                <div className="bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-gray-300 min-h-[60px]">
                  {resultsData[0]?.hook ? (
                    <><span className="text-[#6366F1] font-bold">"{resultsData[0].hook}"</span><br/><span className="text-xs text-gray-400 mt-1 block">{resultsData[0].description}</span></>
                  ) : (
                    <span className="opacity-50 italic">AI will generate a viral hook...</span>
                  )}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-white/5 border border-white/10 rounded-xl p-3">
                  <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">Voiceover</h4>
                  <p className="text-xs font-medium text-white">AI Real Estate (F)</p>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-xl p-3">
                  <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">Music</h4>
                  <p className="text-xs font-medium text-white">Lo-Fi Chill</p>
                </div>
              </div>

              {resultsData.length > 0 && (
                <a href={`http://localhost:8000${resultsData[0].video_url || resultsData[0].videoUrl || ''}`} download>
                  <Button variant="primary" className="w-full bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] border-none shadow-lg shadow-[#6366F1]/20">
                    <Download size={16} className="mr-2" /> Download HD Video
                  </Button>
                </a>
              )}
            </div>
          </div>

          {/* Processing Steps */}
          {(isProcessing || steps.length > 0) && (
            <div className="glass-card rounded-2xl p-5 mb-6">
              <h3 className="text-sm font-bold text-white mb-4">AI Workflow Status</h3>
              <ProgressStepper steps={steps} currentStep={currentStep} isProcessing={isProcessing} />
            </div>
          )}

          {/* Alternative Variations (If any) */}
          {resultsData.length > 1 && (
            <div className="glass-card rounded-2xl p-5">
              <h3 className="text-sm font-bold text-white mb-3">Other Variations</h3>
              <div className="flex gap-3 overflow-x-auto pb-2 custom-scrollbar">
                {resultsData.slice(1).map((res, i) => (
                  <div key={i} className="w-24 shrink-0 rounded-lg overflow-hidden border border-[#22252A] relative group cursor-pointer hover:border-[#8B5CF6] transition">
                    <video src={`http://localhost:8000${res.videoUrl || res.video_url || ''}`} className="w-full aspect-[9/16] object-cover opacity-60 group-hover:opacity-100 transition" />
                    <div className="absolute inset-0 flex items-center justify-center bg-black/40 group-hover:bg-transparent transition">
                      <Play size={16} fill="white" className="opacity-80" />
                    </div>
                    <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black to-transparent p-1">
                      <p className="text-[9px] font-bold text-white text-center truncate">{res.style}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
        </div>
      </div>

    </div>
  );
}
