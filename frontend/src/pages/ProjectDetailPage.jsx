import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { UploadCloud, GripVertical, Download, X, Link2, Plus, Loader2 } from 'lucide-react';
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

  const [reelDuration, setReelDuration] = useState('30 sec');
  const [reelStyle, setReelStyle] = useState('Luxury');

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
    }, 3000);
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
    // Optimistic UI
    setUploads((prev) => prev.filter((u) => u._id !== uploadId));
    try {
      await apiFetch(`/projects/${id}/uploads/${uploadId}`, { method: 'DELETE' });
    } catch {
      fetchProjectData(); // revert on failure
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
    
    // Refresh to show newly uploaded files
    fetchProjectData();
    // Clear input
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
      fetchProjectData(); // revert
    }
  };

  // --- Analyze Phase ---
  const handleAnalyze = () => {
    if (!project?.title?.trim()) {
      setLocalError('Enter a property name.');
      return;
    }
    const readyClips = uploads.filter(u => u.status === 'PROCESSED');
    if (readyClips.length < 3) {
      setLocalError(`Add at least 3 clips. Currently ${readyClips.length} ready.`);
      return;
    }
    setLocalError('');

    const params = new URLSearchParams();
    params.append('duration', reelDuration);
    params.append('style', reelStyle);

    const token = getAccessToken() || '';
    start(`http://localhost:8000/api/v1/projects/${id}/generation/analyze?${params.toString()}&token=${token}`);
  };

  // --- Generate Phase ---
  const handleGenerateReel = () => {
    const params = new URLSearchParams();
    params.append('duration', reelDuration);
    params.append('style', reelStyle);

    const token = getAccessToken() || '';
    start(`http://localhost:8000/api/v1/projects/${id}/generation/generate?${params.toString()}&token=${token}`);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  const displayError = localError || error;
  const resultsData = result?.results || [];

  const tabs = [
    { id: 'links', label: 'Video Links', icon: Link2 },
    { id: 'dropbox', label: 'Dropbox Folder', icon: UploadCloud },
    { id: 'upload', label: 'Local Upload', icon: UploadCloud },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="max-w-[1100px]">
      <div className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight mb-1">Create Property Reel</h1>
        <p className="text-gray-500">Upload clips, organize your story, and render a cinematic reel.</p>
      </div>

      {displayError && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 px-5 py-4 rounded-2xl text-sm mb-8 flex items-center justify-between">
          <span>{displayError}</span>
          <button onClick={() => setLocalError('')} className="text-red-400 hover:text-red-300"><X size={16} /></button>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* ──── LEFT COLUMN ──── */}
        <div className="xl:col-span-7 flex flex-col gap-6">

          {/* Project Setup */}
          <Card className="p-7">
            <h2 className="text-lg font-semibold mb-5 flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-bold">1</span>
              Project Setup
            </h2>
            <div className="mb-5">
              <label className="block text-sm text-gray-400 mb-2">Property Name</label>
              <input
                type="text"
                defaultValue={project?.title || ''}
                onBlur={handleTitleBlur}
                placeholder="e.g. Skyline Residences, Ahmedabad"
                className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-600 focus:outline-none focus:border-blue-500/50 transition text-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Duration</label>
                <select value={reelDuration} onChange={(e) => setReelDuration(e.target.value)} className="w-full bg-[#0c0c0c] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/50 transition cursor-pointer">
                  <option value="20 sec">20 Seconds</option>
                  <option value="30 sec">30 Seconds</option>
                  <option value="45 sec">45 Seconds</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Style</label>
                <select value={reelStyle} onChange={(e) => setReelStyle(e.target.value)} className="w-full bg-[#0c0c0c] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/50 transition cursor-pointer">
                  <option value="Luxury">Luxury</option>
                  <option value="Cinematic">Cinematic</option>
                  <option value="Modern">Modern Property Tour</option>
                  <option value="Viral">Instagram Viral</option>
                </select>
              </div>
            </div>
          </Card>

          {/* Upload Clips */}
          <Card className="p-7">
            <h2 className="text-lg font-semibold mb-5 flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-bold">2</span>
              Upload Clips
            </h2>
            <div className="flex gap-1 bg-white/[0.03] p-1.5 rounded-xl border border-white/5 mb-5">
              {tabs.map((tab) => (
                <button key={tab.id} onClick={() => setUploadMode(tab.id)} className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition ${uploadMode === tab.id ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-white'}`}>
                  <tab.icon size={15} />{tab.label}
                </button>
              ))}
            </div>
            {uploadMode === 'links' && (
              <div className="flex gap-3">
                <input type="text" value={urlInput} onChange={(e) => setUrlInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Paste a Dropbox video URL..." className="flex-1 bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-600 text-sm focus:outline-none focus:border-blue-500/50 transition" />
                <Button variant="gradient" size="md" onClick={addUrl}><Plus size={16} />Add</Button>
              </div>
            )}
            
            {uploadMode === 'dropbox' && (
              <div className="flex gap-3">
                <input type="text" value={urlInput} onChange={(e) => setUrlInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Paste a Dropbox folder URL..." className="flex-1 bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-600 text-sm focus:outline-none focus:border-blue-500/50 transition" />
                <Button variant="gradient" size="md" onClick={addUrl}><Plus size={16} />Import</Button>
              </div>
            )}
            
            {uploadMode === 'upload' && (
              <div className="flex flex-col items-center justify-center p-8 border border-dashed border-white/20 rounded-xl bg-white/[0.01]">
                <UploadCloud size={32} className="text-gray-500 mb-3" />
                <p className="text-sm font-medium mb-1">Upload local video files here</p>
                <p className="text-xs text-gray-500 mb-4">MP4, MOV</p>
                <input 
                  type="file" 
                  id="local-file-upload" 
                  className="hidden" 
                  multiple 
                  accept="video/mp4,video/quicktime"
                  onChange={handleLocalUpload}
                />
                <Button variant="outline" size="sm" onClick={() => document.getElementById('local-file-upload').click()}>
                  Browse Files
                </Button>
              </div>
            )}
            {uploads.length > 0 && <p className="text-xs text-gray-500 mt-3">{uploads.length} clip{uploads.length !== 1 && 's'} added</p>}
          </Card>
        </div>

        {/* ──── RIGHT COLUMN ──── */}
        <div className="xl:col-span-5 flex flex-col gap-6">
          <Card className="p-7 flex flex-col">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <span className="w-6 h-6 rounded-md bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-bold">3</span>
                Story Builder
              </h2>
            </div>
            <div className="space-y-2 flex-1 min-h-[180px] mb-6">
              {uploads.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-600 py-10">
                  <p className="text-sm">Add video URLs to build your timeline.</p>
                </div>
              ) : (
                uploads.map((item, idx) => (
                  <motion.div key={item._id} layout draggable onDragStart={() => handleDragStart(idx)} onDragOver={handleDragOver} onDrop={() => handleDrop(idx)} className="flex items-center gap-3 p-3 rounded-xl border border-white/[0.06] bg-white/[0.02] cursor-grab active:cursor-grabbing hover:border-white/15 transition group">
                    <div className="flex-1 min-w-0 flex items-center justify-between">
                      <div className="flex-1 min-w-0 pr-2">
                        <p className="text-sm font-medium truncate">{item.filename}</p>
                        <p className="text-[11px] text-gray-600 truncate">{item.originalUrl}</p>
                      </div>
                      <div className="shrink-0">
                        {item.status === 'PENDING' && <span className="text-xs text-gray-500 bg-gray-500/10 px-2 py-1 rounded">Pending</span>}
                        {item.status === 'PROCESSING' && <span className="text-xs text-blue-400 bg-blue-400/10 px-2 py-1 rounded flex items-center gap-1"><Loader2 size={10} className="animate-spin" /> Processing</span>}
                        {item.status === 'PROCESSED' && <span className="text-xs text-green-400 bg-green-400/10 px-2 py-1 rounded">Ready</span>}
                        {item.status === 'FAILED' && <span className="text-xs text-red-400 bg-red-400/10 px-2 py-1 rounded" title={item.error}>Failed</span>}
                      </div>
                    </div>
                    <button onClick={() => removeClip(item._id)} className="w-7 h-7 rounded-lg flex items-center justify-center text-gray-600 hover:text-red-400 hover:bg-red-400/10 transition opacity-0 group-hover:opacity-100">
                      <X size={14} />
                    </button>
                    <GripVertical size={16} className="text-gray-700 group-hover:text-gray-500 transition shrink-0" />
                  </motion.div>
                ))
              )}
            </div>
            
            {project?.draftTimeline ? (
              <div className="mb-4">
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 mb-4">
                  <h3 className="text-blue-400 font-bold text-sm mb-2">AI Suggested Storyline</h3>
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                    {project.draftTimeline.map((clip, i) => (
                      <div key={i} className="flex gap-3 text-sm">
                        <span className="text-gray-500">{i+1}.</span>
                        <div className="flex-1">
                          <p className="text-white font-medium">{clip.room}</p>
                          <p className="text-gray-400 text-xs">{clip.reason}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <Button variant="gradient" size="lg" className="w-full" onClick={handleGenerateReel} disabled={isProcessing} loading={isProcessing}>
                  {isProcessing ? 'Rendering Video...' : 'Generate Reel'}
                </Button>
              </div>
            ) : (
              <Button variant="primary" size="lg" className="w-full" onClick={handleAnalyze} disabled={isProcessing} loading={isProcessing}>
                {isProcessing ? 'Analyzing...' : 'Analyze & Build Story'}
              </Button>
            )}
          </Card>

          {(isProcessing || steps.length > 0) && (
            <Card className="p-7 border-blue-500/20">
              <h2 className="text-lg font-semibold mb-4">Processing</h2>
              <ProgressStepper steps={steps} currentStep={currentStep} isProcessing={isProcessing} />
            </Card>
          )}

          {resultsData.length > 0 && (
            <Card className="p-7 border-green-500/20">
              <h2 className="text-lg font-semibold mb-4 text-green-400">Reels Ready</h2>
              <div className="space-y-8">
                {resultsData.map((resItem, i) => {
                  const vUrl = `http://localhost:8000${resItem.video_url || resItem.videoUrl || ''}`;
                  return (
                    <div key={i} className="border border-white/10 p-4 rounded-xl bg-white/[0.02]">
                      <h3 className="font-bold text-base mb-2 text-white flex items-center gap-2">
                        {resItem.style || "Reel"} Variation
                      </h3>
                      {resItem.hook && <p className="text-sm font-semibold text-blue-300 italic mb-1">"{resItem.hook}"</p>}
                      {resItem.description && <p className="text-xs text-gray-400 mb-2 whitespace-pre-line">{resItem.description}</p>}
                      {resItem.hashtags && <p className="text-xs text-blue-500 mb-3">{resItem.hashtags.join(' ')}</p>}
                      
                      <video src={vUrl} controls className="w-full rounded-xl border border-white/10 bg-black mb-4 aspect-[9/16] object-contain max-h-[380px]" />
                      <a href={vUrl} download><Button variant="primary" size="md" className="w-full"><Download size={16} /> Download {resItem.style}</Button></a>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}
        </div>
      </div>
    </motion.div>
  );
}
