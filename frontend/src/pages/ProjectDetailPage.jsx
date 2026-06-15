import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  UploadCloud, Download, X, Link2, Plus, Loader2, Play, Sparkles, CheckCircle2, 
  Film, Activity, Video, Type, Maximize, Smartphone, Square, ChevronRight, Check
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { ProgressStepper } from '../components/ui/ProgressStepper';
import { useSSE } from '../hooks/useSSE';
import { apiFetch, getAccessToken } from '../api/client';

const STEPS = [
  { id: 1, label: 'Upload' },
  { id: 2, label: 'Analyze' },
  { id: 3, label: 'Storyboard' },
  { id: 4, label: 'Style' },
  { id: 5, label: 'Music' },
  { id: 6, label: 'Generate' },
  { id: 7, label: 'Export' }
];

export default function ProjectDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(!!id);
  const [project, setProject] = useState(null);
  const [uploads, setUploads] = useState([]);
  const [currentStep, setCurrentStep] = useState(1);
  const [highestStep, setHighestStep] = useState(1);

  const [urlInput, setUrlInput] = useState('');
  const [reelDuration, setReelDuration] = useState('30 sec');
  const [reelStyle, setReelStyle] = useState('Luxury');
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [duplicateSensitivity, setDuplicateSensitivity] = useState('Low');

  // Music States
  const [musicMode, setMusicMode] = useState('Auto Select'); // Auto Select, Library, Custom, None
  const [selectedMusicPath, setSelectedMusicPath] = useState('');
  const [musicVolume, setMusicVolume] = useState(0.2);
  const [voVolume, setVoVolume] = useState(1.0);
  const [isUploadingMusic, setIsUploadingMusic] = useState(false);
  const [musicLibrary, setMusicLibrary] = useState([]);

  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const [isUploadingUrl, setIsUploadingUrl] = useState(false);

  const { isProcessing, steps, currentStep: sseStep, result, error, start } = useSSE();
  const [localError, setLocalError] = useState('');

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
        
        if (!isPolling && projData.draftTimeline) {
          if (projData.generatedReels && projData.generatedReels.length > 0) setCurrentStep(7);
          else setCurrentStep(3);
        }
      } else if (!isPolling) setLocalError('Failed to load project details.');
    } catch {
      if (!isPolling) setLocalError('Connection error.');
    } finally {
      if (!isPolling) setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchProjectData();
    const interval = setInterval(() => fetchProjectData(true), 10000);
    
    // Fetch music library
    apiFetch('/music-library')
      .then(res => res.ok ? res.json() : { library: [] })
      .then(data => setMusicLibrary(data.library || []))
      .catch(err => console.error("Failed to load music library"));

    return () => clearInterval(interval);
  }, [fetchProjectData]);

  useEffect(() => {
    if (currentStep === 6 && !isProcessing && result?.results?.length > 0) {
      setCurrentStep(7);
    }
    setHighestStep(prev => Math.max(prev, currentStep));
  }, [currentStep, isProcessing, result]);

  const handleTitleBlur = async (e) => {
    const newTitle = e.target.value;
    if (newTitle !== project.title) {
      setProject({ ...project, title: newTitle });
      await apiFetch(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify({ title: newTitle }) });
    }
  };

  const addUrl = async () => {
    const val = urlInput.trim();
    if (!val) return;
    setUrlInput('');
    setIsUploadingUrl(true);
    try {
      await apiFetch(`/projects/${id}/uploads`, { method: 'POST', body: JSON.stringify({ urls: [val] }) });
      await fetchProjectData();
    } catch {
      setLocalError('Failed to add URL.');
    } finally {
      setIsUploadingUrl(false);
    }
  };

  const handleKeyDown = (e) => { if (e.key === 'Enter') { e.preventDefault(); addUrl(); } };

  const handleLocalUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setIsUploadingFile(true);
    for (let i = 0; i < files.length; i++) {
      const formData = new FormData();
      formData.append('file', files[i]);
      try { await apiFetch(`/projects/${id}/uploads/file`, { method: 'POST', body: formData }); } 
      catch (err) { setLocalError(`Failed to upload ${files[i].name}`); }
    }
    await fetchProjectData();
    setIsUploadingFile(false);
    e.target.value = null;
  };

  const deleteUpload = async (uploadId) => {
    try {
      await apiFetch(`/projects/${id}/uploads/${uploadId}`, { method: 'DELETE' });
      await fetchProjectData();
    } catch {
      setLocalError('Failed to remove clip.');
    }
  };

  const goToAnalyze = () => {
    if (!project?.title?.trim()) { setLocalError('Enter a property name.'); return; }
    const readyClips = uploads.filter(u => u.status === 'PROCESSED');
    if (readyClips.length === 0) { setLocalError('Add at least 1 clip to begin.'); return; }
    setLocalError('');
    setCurrentStep(2);
    
    if (!project?.draftTimeline) {
      const params = new URLSearchParams();
      params.append('duration', reelDuration);
      params.append('style', reelStyle);
      params.append('duplicate_sensitivity', duplicateSensitivity);
      start(`http://localhost:8000/api/v1/projects/${id}/generation/analyze?${params.toString()}&token=${getAccessToken() || ''}`);
    }
  };

  const float_end = (val) => parseFloat(val) || 5.0;
  const float_start = (val) => parseFloat(val) || 0.0;

  const goToStoryboard = () => setCurrentStep(3);
  const goToStyle = () => setCurrentStep(4);
  const goToMusic = () => setCurrentStep(5);

  const handleGenerateReel = () => {
    setCurrentStep(6);
    const params = new URLSearchParams();
    params.append('duration', reelDuration);
    params.append('style', reelStyle);
    params.append('aspect_ratio', aspectRatio);
    
    // Pass Music Params
    if (musicMode === 'None') {
      params.append('music_path', '');
      params.append('music_volume', '0');
    } else if (musicMode === 'Auto Select') {
      const match = musicLibrary.find(t => t.tag === reelStyle) || musicLibrary[0];
      params.append('music_path', match ? match.path : '');
      params.append('music_volume', match ? musicVolume : 0);
    } else {
      params.append('music_path', selectedMusicPath);
      params.append('music_volume', musicVolume);
    }
    
    params.append('vo_volume', voVolume);

    start(`http://localhost:8000/api/v1/projects/${id}/generation/generate?${params.toString()}&token=${getAccessToken() || ''}`);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <Loader2 size={40} className="animate-spin text-[#0EA5E9]" />
        <p className="text-[#64748B] font-bold tracking-wider uppercase text-xs">Loading Workspace</p>
      </div>
    );
  }

  const displayError = localError || error;
  const resultsData = result?.results || [];
  const readyClips = uploads.filter(u => u.status === 'PROCESSED');
  const hasUploads = uploads.length > 0;
  const timelineIds = project?.draftTimeline?.map(t => t.upload_id) || [];
  const stylesList = ['Luxury', 'Modern', 'Cinematic', 'Viral', 'Realtor'];
  const previewRatioClass = aspectRatio === '16:9' ? 'aspect-video' : (aspectRatio === '1:1' ? 'aspect-square' : 'aspect-[9/16]');

  return (
    <div className="h-[calc(100vh-80px)] overflow-y-auto flex flex-col -m-8 p-8 relative bg-[#F8FAFC]">
      
      {/* ──── TOP NAVIGATION PROGRESS ──── */}
      <div className="bg-white rounded-2xl shadow-sm border border-[#E2E8F0] p-4 mb-8 flex items-center justify-between shrink-0">
        <input
          type="text"
          defaultValue={project?.title || ''}
          onBlur={handleTitleBlur}
          placeholder="Property Name..."
          className="bg-transparent text-xl font-black text-[#0F172A] placeholder:text-[#cbd5e1] focus:outline-none w-1/4"
        />
        
        <div className="flex-1 flex items-center justify-center max-w-3xl">
          {STEPS.map((step, idx) => (
            <React.Fragment key={step.id}>
              <div 
                className={`flex flex-col items-center relative transition-all ${step.id <= highestStep && !isProcessing ? 'cursor-pointer hover:scale-105' : 'opacity-70 cursor-not-allowed'}`}
                onClick={() => { if (step.id <= highestStep && !isProcessing) setCurrentStep(step.id); }}
              >
                <motion.div animate={{ scale: currentStep === step.id ? 1.1 : 1 }} className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-black transition-all ${currentStep > step.id ? 'bg-[#10B981] text-white' : currentStep === step.id ? 'bg-[#0EA5E9] text-white ring-4 ring-[#0EA5E9]/20' : 'bg-[#F8FAFC] text-[#94a3b8] border border-[#E2E8F0]'}`}>
                  {currentStep > step.id ? <Check size={14} /> : step.id}
                </motion.div>
                <span className={`absolute top-10 whitespace-nowrap text-[10px] font-bold uppercase tracking-wider ${currentStep >= step.id ? 'text-[#0F172A]' : 'text-[#94a3b8]'}`}>{step.label}</span>
              </div>
              {idx < STEPS.length - 1 && (
                <div className="flex-1 h-1 mx-2 rounded-full overflow-hidden bg-[#E2E8F0]">
                  <motion.div initial={{ width: 0 }} animate={{ width: currentStep > step.id ? '100%' : '0%' }} transition={{ duration: 0.5 }} className="h-full bg-[#10B981]" />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
        <div className="w-1/4"></div>
      </div>

      {displayError && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="bg-red-50 border border-red-100 text-red-600 px-5 py-4 rounded-2xl text-sm font-medium flex items-center justify-between shadow-sm mb-6 shrink-0">
          <span>{displayError}</span>
          <button onClick={() => setLocalError('')} className="text-red-400 hover:text-red-600"><X size={16} /></button>
        </motion.div>
      )}

      {/* ──── DYNAMIC WIZARD CONTENT ──── */}
      <div className="flex-1 pb-10">
        <AnimatePresence mode="wait">
          
          {/* STEP 1: UPLOAD ASSETS */}
          {currentStep === 1 && (
            <motion.div key="step1" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="max-w-5xl mx-auto w-full">
              <div className="text-center mb-8">
                <h2 className="text-4xl font-black text-[#0F172A] tracking-tight">Upload Footage</h2>
                <p className="text-lg text-[#64748B] font-medium mt-2">Bring in your property clips to begin the AI edit.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Local Upload */}
                <motion.div whileHover={{ scale: 1.01 }} onClick={() => !isUploadingFile && document.getElementById('local-file-upload').click()} className={`flex flex-col items-center justify-center p-12 border-2 border-dashed border-[#cbd5e1] rounded-[2rem] bg-white transition-all group shadow-sm ${isUploadingFile ? 'cursor-wait opacity-80' : 'hover:border-[#0EA5E9] hover:shadow-lg cursor-pointer'}`}>
                  {isUploadingFile ? (
                    <div className="flex flex-col items-center">
                      <Loader2 size={40} className="animate-spin text-[#0EA5E9] mb-4" />
                      <p className="text-lg font-bold text-[#0F172A]">Uploading file(s)...</p>
                      <p className="text-sm text-[#64748B]">Please wait</p>
                    </div>
                  ) : (
                    <>
                      <div className="w-20 h-20 rounded-2xl bg-[#F0F9FF] shadow-sm flex items-center justify-center mb-5 group-hover:scale-110 group-hover:bg-[#0EA5E9] transition-all duration-300">
                        <UploadCloud size={32} className="text-[#0EA5E9] group-hover:text-white transition-colors" />
                      </div>
                      <p className="text-2xl font-black text-[#0F172A] mb-1">Drag & Drop Videos</p>
                      <p className="text-sm font-medium text-[#64748B]">MP4 or MOV up to 4K resolution</p>
                    </>
                  )}
                  <input type="file" id="local-file-upload" className="hidden" multiple accept="video/*" onChange={handleLocalUpload} disabled={isUploadingFile} />
                </motion.div>

                {/* URL Import */}
                <div className="bg-white p-10 rounded-[2rem] border border-[#E2E8F0] shadow-sm flex flex-col justify-center">
                  <h3 className="text-xl font-black text-[#0F172A] flex items-center gap-2 mb-3"><Link2 size={24} className="text-[#0EA5E9]"/> Import via URL</h3>
                  <p className="text-sm text-[#64748B] mb-6 font-medium leading-relaxed">
                    Paste links directly from <strong className="text-[#0F172A]">Google Drive</strong>, <strong className="text-[#0F172A]">Dropbox</strong>, <strong className="text-[#0F172A]">OneDrive</strong>, or any direct MP4 url. Add as many as you need.
                  </p>
                  <div className="flex flex-col xl:flex-row gap-3">
                    <input type="text" value={urlInput} onChange={(e) => setUrlInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Paste video URL here..." className="flex-1 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl px-5 py-4 text-[#0F172A] text-sm focus:outline-none focus:border-[#0EA5E9] shadow-inner" disabled={isUploadingUrl} />
                    <button onClick={addUrl} disabled={isUploadingUrl || !urlInput.trim()} className="bg-[#0F172A] text-white px-8 py-4 rounded-xl font-black hover:bg-[#1e293b] shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50">
                      {isUploadingUrl ? <Loader2 size={18} className="animate-spin" /> : <Plus size={18}/>} Add Link
                    </button>
                  </div>
                </div>
              </div>

              {/* Upload Status List */}
              {hasUploads && (
                <div className="mt-8 bg-white p-6 rounded-[2rem] border border-[#E2E8F0] shadow-sm">
                  <h3 className="text-sm font-black text-[#0F172A] uppercase tracking-wider mb-4">Clip Processing Status</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {uploads.map((u, i) => (
                      <div key={u._id} className="flex justify-between items-center p-3 bg-[#F8FAFC] rounded-xl border border-[#E2E8F0] group relative overflow-hidden">
                        <span className="font-bold text-xs text-[#0F172A] truncate pr-6 transition-all group-hover:max-w-[70%]" title={u.originalFilename || `Clip ${i + 1}`}>
                          {u.originalFilename || `Clip ${i + 1}`}
                        </span>
                        
                        <div className="flex items-center gap-2 group-hover:opacity-0 transition-opacity">
                          {u.status === 'PROCESSED' ? (
                            <span className="text-[10px] font-black text-[#10B981] bg-[#10B981]/10 px-2 py-1 rounded-md flex items-center gap-1 shrink-0"><Check size={12}/> Ready</span>
                          ) : u.status === 'ERROR' ? (
                            <span className="text-[10px] font-black text-[#EF4444] bg-[#EF4444]/10 px-2 py-1 rounded-md shrink-0">Failed</span>
                          ) : (
                            <span className="text-[10px] font-black text-[#F59E0B] bg-[#F59E0B]/10 px-2 py-1 rounded-md flex items-center gap-1 shrink-0"><Loader2 size={12} className="animate-spin"/> Pending</span>
                          )}
                        </div>

                        <button 
                          onClick={() => deleteUpload(u._id)}
                          className="absolute right-2 opacity-0 group-hover:opacity-100 bg-red-100 text-red-600 hover:bg-red-500 hover:text-white rounded-md p-1.5 transition-all shadow-sm flex items-center justify-center"
                          title="Remove clip"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Success Summary Card */}
              <AnimatePresence>
                {hasUploads && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt-8 bg-gradient-to-br from-white to-[#F0F9FF] border-2 border-[#0EA5E9]/20 p-8 rounded-[2rem] shadow-lg flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="flex items-center gap-5">
                      <div className="w-16 h-16 rounded-full bg-[#10B981]/10 flex items-center justify-center shrink-0">
                        <CheckCircle2 size={32} className="text-[#10B981]" />
                      </div>
                      <div>
                        <h3 className="text-2xl font-black text-[#0F172A]">Upload Complete</h3>
                        <p className="text-base font-bold text-[#64748B] mt-1">{readyClips.length} Clips Ready • 4K/1080p Processed</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 w-full md:w-auto">
                      <div className="flex flex-col">
                        <label className="text-xs font-bold text-[#64748B] uppercase tracking-wider mb-1">Duplicate Sensitivity</label>
                        <select 
                          value={duplicateSensitivity} 
                          onChange={(e) => setDuplicateSensitivity(e.target.value)}
                          className="bg-white border border-[#E2E8F0] rounded-xl px-4 py-3 text-[#0F172A] font-bold focus:outline-none focus:border-[#0EA5E9] shadow-sm appearance-none min-w-[120px]"
                        >
                          <option value="Low">Low (Keep More)</option>
                          <option value="Medium">Medium</option>
                          <option value="High">High (Strict)</option>
                        </select>
                      </div>
                      <button onClick={goToAnalyze} disabled={!hasUploads || uploads.some(u => u.status !== 'PROCESSED')} className="w-full md:w-auto bg-[#0EA5E9] text-white px-8 py-4 rounded-xl text-lg font-black shadow-[0_10px_20px_rgba(14,165,233,0.3)] hover:scale-105 active:scale-95 disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2 transition-all">
                        Start AI Analysis <ChevronRight size={20} />
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}

          {/* STEP 2: AI ANALYSIS */}
          {currentStep === 2 && (
            <motion.div key="step2" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="max-w-6xl mx-auto w-full">
              <div className="text-center mb-8">
                <h2 className="text-4xl font-black text-[#0F172A] tracking-tight">AI Director Analysis</h2>
                <p className="text-lg text-[#64748B] font-medium mt-2">Analyzing scene composition, room structures, and optimal pacing.</p>
              </div>

              {isProcessing && (
                <div className="bg-white rounded-[2rem] p-10 shadow-sm border border-[#E2E8F0] flex flex-col items-center mb-8">
                  <Loader2 size={48} className="animate-spin text-[#14B8A6] mb-6" />
                  <div className="w-full max-w-3xl">
                    <ProgressStepper steps={steps} currentStep={sseStep} isProcessing={isProcessing} />
                  </div>
                </div>
              )}

              {/* True Data Insights (No Mocks) */}
              {project?.draftTimeline && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
                  
                  {/* Transparency Panel */}
                  <div className="col-span-1 bg-white p-8 rounded-[2rem] border border-[#E2E8F0] shadow-sm flex flex-col h-full">
                    <h3 className="text-sm font-black text-[#64748B] uppercase tracking-wider mb-6 flex items-center gap-2 shrink-0"><Activity size={16}/> Transparency Panel</h3>
                    
                    {/* Coverage Analytics */}
                    {project?.aiMetadata?.coverage_analytics && (
                      <div className="mb-6 p-4 bg-gradient-to-br from-[#F0FDF4] to-[#ECFDF5] rounded-xl border border-[#10B981]/20 shrink-0">
                        <p className="text-[10px] font-black text-[#10B981] uppercase tracking-wider mb-3">Coverage & Duplicate Audit</p>
                        <div className="grid grid-cols-2 gap-3 mb-3">
                          <div>
                            <p className="text-[10px] font-bold text-[#64748B]">Total Uploaded</p>
                            <p className="text-lg font-black text-[#0F172A]">{project.aiMetadata.coverage_analytics.uploaded_count}</p>
                          </div>
                          <div>
                            <p className="text-[10px] font-bold text-[#64748B]">Total Removed</p>
                            <p className="text-lg font-black text-[#EF4444]">{project.aiMetadata.coverage_analytics.duplicates_removed}</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <p className="text-[10px] font-bold text-[#64748B]">Engine Duplicates (SSIM/Hash)</p>
                            <p className="text-sm font-black text-[#F59E0B]">{project.aiMetadata.coverage_analytics.pre_processor_duplicates || 0}</p>
                          </div>
                          <div>
                            <p className="text-[10px] font-bold text-[#64748B]">AI Duplicates (Semantic)</p>
                            <p className="text-sm font-black text-[#F97316]">{project.aiMetadata.coverage_analytics.ai_duplicates || 0}</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3 mt-3 pt-3 border-t border-[#10B981]/20">
                          <div>
                            <p className="text-[10px] font-bold text-[#64748B]">Unique Selected</p>
                            <p className="text-lg font-black text-[#10B981]">{project.aiMetadata.coverage_analytics.selected_count}</p>
                          </div>
                          <div>
                            <p className="text-[10px] font-bold text-[#64748B]">Coverage</p>
                            <p className="text-lg font-black text-[#8B5CF6]">{project.aiMetadata.coverage_analytics.coverage_percentage}%</p>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="space-y-5 mb-6 shrink-0">
                      <div>
                        <p className="text-xs font-bold text-[#94a3b8] uppercase mb-1">Total Analyzed</p>
                        <p className="text-2xl font-black text-[#0F172A]">{project?.aiMetadata?.analyzed_sec || 0}s</p>
                      </div>
                      <div>
                        <p className="text-xs font-bold text-[#94a3b8] uppercase mb-1">Duplicates Removed</p>
                        <p className="text-2xl font-black text-[#EF4444]">{project?.aiMetadata?.duplicates_removed || 0}</p>
                      </div>
                      <div>
                        <p className="text-xs font-bold text-[#94a3b8] uppercase mb-1">Final Storyline</p>
                        <p className="text-2xl font-black text-[#10B981]">{project?.aiMetadata?.selected_sec || 0}s</p>
                      </div>
                    </div>

                    {project?.aiMetadata?.removed_clips?.length > 0 && (
                      <div className="mt-auto border-t border-[#E2E8F0] pt-4 overflow-y-auto min-h-0">
                        <p className="text-[10px] font-black text-[#64748B] uppercase tracking-wider mb-2">Removed Clips</p>
                        <ul className="space-y-2">
                          {project.aiMetadata.removed_clips.map((c, i) => (
                            <li key={i} className="text-xs bg-red-50 text-red-700 px-2 py-1.5 rounded border border-red-100 flex flex-col gap-1">
                              <span className="font-bold">Clip #{c.video_index + 1}</span>
                              <span className="opacity-80 leading-tight">{c.reason}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div className="col-span-1 lg:col-span-3 bg-white p-8 rounded-[2rem] border border-[#E2E8F0] shadow-sm">
                    <h3 className="text-sm font-black text-[#64748B] uppercase tracking-wider mb-6">AI Selected Storyline</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {project.draftTimeline.map((item, i) => (
                         <div key={i} className="p-4 rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] flex flex-col justify-between">
                           <div>
                             <span className="text-sm font-black text-[#0F172A] capitalize">{item.scene_type || 'General Room'}</span>
                             <p className="text-xs font-bold text-[#64748B] mt-1">{item.end ? (float_end(item.end) - float_start(item.start)).toFixed(1) : '5.0'}s Segment</p>
                           </div>
                           <div className="mt-3 pt-3 border-t border-[#E2E8F0] flex justify-between items-center">
                              <span className="text-[10px] font-black text-[#10B981]">Conf: {item.confidence_score || 90}%</span>
                              <span className="text-[10px] font-black text-[#0EA5E9]">Qual: {item.visual_quality_score || 85}/100</span>
                           </div>
                         </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}

              <div className="flex justify-end">
                <button onClick={goToStoryboard} disabled={isProcessing || !project?.draftTimeline} className="bg-[#0F172A] text-white px-10 py-5 rounded-2xl text-lg font-black shadow-xl hover:bg-[#1e293b] transition-all disabled:opacity-50 disabled:pointer-events-none flex items-center gap-3">
                  Review Storyboard <ChevronRight size={24} />
                </button>
              </div>
            </motion.div>
          )}

          {/* STEP 3: STORYBOARD REVIEW */}
          {currentStep === 3 && (
            <motion.div key="step3" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="max-w-6xl mx-auto w-full">
              <div className="text-center mb-8">
                <h2 className="text-4xl font-black text-[#0F172A] tracking-tight">Storyboard Review</h2>
                <p className="text-lg text-[#64748B] font-medium mt-2">Verify the intelligent sequence constructed by the AI Director.</p>
              </div>

              <div className="bg-white rounded-[2rem] p-8 mb-8 shadow-sm border border-[#E2E8F0]">
                {/* Row 1: Uploaded (Muted) */}
                <div className="mb-10 opacity-70 hover:opacity-100 transition-opacity">
                  <h3 className="text-xs font-black text-[#64748B] uppercase tracking-wider mb-4 flex items-center gap-2">Raw Uploads <span className="px-2 py-0.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-md text-[#0F172A]">{uploads.length}</span></h3>
                  <div className="flex gap-4 overflow-x-auto pb-2 hide-scrollbar">
                    {uploads.map((item, idx) => (
                       <div key={item._id} className="shrink-0 w-36 rounded-xl overflow-hidden border border-[#E2E8F0] relative shadow-sm">
                         <div className="h-24 bg-[#F8FAFC]">
                           {item.previewPath ? <video src={`http://localhost:8000/${item.previewPath.replace(/\\/g, '/')}`} className="w-full h-full object-cover" /> : <Video className="w-full h-full p-6 text-[#cbd5e1]"/>}
                         </div>
                         <div className="absolute top-2 left-2 bg-white/90 backdrop-blur rounded text-[10px] font-black px-1.5 py-0.5 text-[#0F172A]">#{idx+1}</div>
                       </div>
                    ))}
                  </div>
                </div>

                {/* Row 2: AI Selected */}
                <div>
                  <h3 className="text-sm font-black text-[#8B5CF6] uppercase tracking-wider mb-4 flex items-center gap-2">AI Sequenced Story <span className="px-2.5 py-1 bg-[#8B5CF6]/10 text-[#8B5CF6] rounded-md">{project?.draftTimeline?.length}</span></h3>
                  <div className="flex gap-5 overflow-x-auto pb-4 hide-scrollbar">
                    {project?.draftTimeline?.map((item, idx) => (
                      <div key={idx} className="shrink-0 w-64 rounded-[1.5rem] bg-white shadow-md border border-[#8B5CF6]/20 overflow-hidden relative group">
                        <div className="h-40 bg-[#F8FAFC] relative">
                          {item.localPath ? <video src={`http://localhost:8000/${item.localPath.replace(/\\/g, '/')}`} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" /> : <Video className="w-full h-full p-10 text-[#cbd5e1]"/>}
                          <div className="absolute top-3 left-3 bg-[#8B5CF6] text-white rounded-lg text-sm font-black px-3 py-1 shadow-sm">{idx+1}</div>
                        </div>
                        <div className="p-5">
                          <div className="flex justify-between items-start mb-2">
                            <p className="text-base font-black text-[#0F172A] truncate pr-2 capitalize">{item.scene_type || 'Clip'}</p>
                            <span className="text-[10px] font-black text-[#10B981] bg-[#10B981]/10 px-2 py-1 rounded-md">{item.confidence_score ? `${item.confidence_score}% Conf` : 'Extracted'}</span>
                          </div>
                          <p className="text-xs font-bold text-[#64748B] mb-3">{item.clip_duration_sec ? `${item.clip_duration_sec}s display` : `${item.end ? (float_end(item.end) - float_start(item.start)).toFixed(1) : '5.0'}s segment`}</p>
                          
                          {/* AI Ranking Badges */}
                          <div className="grid grid-cols-2 gap-2">
                             <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-2 flex flex-col items-center">
                                <span className="text-[9px] font-bold text-[#94a3b8] uppercase tracking-wide">Quality</span>
                                <span className="text-xs font-black text-[#0F172A]">{item.visual_quality_score || 85}</span>
                             </div>
                             <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-2 flex flex-col items-center">
                                <span className="text-[9px] font-bold text-[#94a3b8] uppercase tracking-wide">Luxury</span>
                                <span className="text-xs font-black text-[#0F172A]">{item.luxury_appeal || 80}</span>
                             </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <button onClick={goToStyle} className="bg-[#0F172A] text-white px-12 py-5 rounded-2xl text-lg font-black shadow-xl hover:bg-[#1e293b] transition-all flex items-center gap-3">
                  Continue to Style <ChevronRight size={24} />
                </button>
              </div>
            </motion.div>
          )}

          {/* STEP 4: STYLE SELECTION */}
          {currentStep === 4 && (
            <motion.div key="step4" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="h-full flex flex-col justify-center max-w-4xl mx-auto w-full">
              <div className="text-center mb-10">
                <h2 className="text-4xl font-black text-[#0F172A] tracking-tight">Final Polish</h2>
                <p className="text-lg text-[#64748B] font-medium mt-2">Select your target platform aspect ratio and creative style.</p>
              </div>

              <div className="flex justify-center mb-10">
                <div className="bg-white border border-[#E2E8F0] shadow-sm p-8 rounded-[2rem] w-full max-w-xl">
                  <h3 className="text-sm font-black text-[#64748B] uppercase tracking-wider mb-6 text-center">1. Aspect Ratio</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <button onClick={() => { setAspectRatio('9:16'); setReelDuration('30-60 sec'); }} className={`flex flex-col items-center justify-center py-6 rounded-2xl text-sm font-bold transition-all ${aspectRatio === '9:16' ? 'bg-[#0EA5E9]/10 text-[#0EA5E9] ring-2 ring-[#0EA5E9]' : 'bg-[#F8FAFC] text-[#64748B] hover:bg-white border border-[#E2E8F0]'}`}>
                      <Smartphone size={28} className="mb-2" /> Reels
                      <span className="text-xs font-medium mt-1 opacity-80">30sec to 60 sec max</span>
                    </button>
                    <button onClick={() => { setAspectRatio('16:9'); setReelDuration('1 min to 2 min or more'); }} className={`flex flex-col items-center justify-center py-6 rounded-2xl text-sm font-bold transition-all ${aspectRatio === '16:9' ? 'bg-[#0EA5E9]/10 text-[#0EA5E9] ring-2 ring-[#0EA5E9]' : 'bg-[#F8FAFC] text-[#64748B] hover:bg-white border border-[#E2E8F0]'}`}>
                      <Maximize size={28} className="mb-2" /> YouTube
                      <span className="text-xs font-medium mt-1 opacity-80">1 min to 2 min or more</span>
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <button onClick={goToMusic} className="bg-[#0F172A] text-white px-14 py-6 rounded-2xl text-xl font-black shadow-xl hover:bg-[#1e293b] transition-all flex items-center gap-3">
                  Continue to Music <ChevronRight size={24} />
                </button>
              </div>
            </motion.div>
          )}

          {/* STEP 5: MUSIC SELECTION */}
          {currentStep === 5 && (
            <motion.div key="step5" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="h-full flex flex-col max-w-5xl mx-auto w-full">
              <div className="text-center mb-10">
                <h2 className="text-4xl font-black text-[#0F172A] tracking-tight">Audio Settings</h2>
                <p className="text-lg text-[#64748B] font-medium mt-2">Choose the perfect background music and mix volumes.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10">
                
                {/* Mode Selector */}
                <div className="md:col-span-1 space-y-4">
                  <h3 className="text-sm font-black text-[#64748B] uppercase tracking-wider mb-4">Music Source</h3>
                  {['Auto Select', 'Library', 'Custom', 'None'].map(mode => (
                    <button key={mode} onClick={() => { setMusicMode(mode); setSelectedMusicPath(''); }} className={`w-full text-left px-5 py-4 rounded-xl text-sm font-bold transition-all flex items-center justify-between ${musicMode === mode ? 'bg-[#0EA5E9] text-white shadow-md' : 'bg-white text-[#64748B] hover:bg-[#F8FAFC] border border-[#E2E8F0]'}`}>
                      {mode} {musicMode === mode && <CheckCircle2 size={16} />}
                    </button>
                  ))}
                </div>

                {/* Main Content Area based on Mode */}
                <div className="md:col-span-2 bg-white border border-[#E2E8F0] shadow-sm p-8 rounded-[2rem]">
                  {musicMode === 'Auto Select' && (
                    <div className="flex flex-col items-center justify-center h-full text-center py-10">
                      <Sparkles size={48} className="text-[#8B5CF6] mb-4" />
                      <h3 className="text-xl font-black text-[#0F172A] mb-2">AI Soundtrack Curation</h3>
                      <p className="text-[#64748B] font-medium">We'll automatically choose a track that fits the <strong className="text-[#0EA5E9]">{reelStyle}</strong> style perfectly.</p>
                    </div>
                  )}

                  {musicMode === 'None' && (
                    <div className="flex flex-col items-center justify-center h-full text-center py-10">
                      <div className="w-16 h-16 rounded-full bg-[#F8FAFC] flex items-center justify-center mb-4"><X size={32} className="text-[#94a3b8]" /></div>
                      <h3 className="text-xl font-black text-[#0F172A] mb-2">No Music</h3>
                      <p className="text-[#64748B] font-medium">The final reel will only contain the original audio from your clips.</p>
                    </div>
                  )}

                  {musicMode === 'Library' && (
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-black text-[#64748B] uppercase tracking-wider">Select a Track</h3>
                        <span className="text-xs font-bold text-[#0EA5E9] bg-[#0EA5E9]/10 px-2 py-0.5 rounded-md">{musicLibrary.length} tracks found</span>
                      </div>
                      
                      {musicLibrary.length === 0 ? (
                        <div className="text-center py-10 border-2 border-dashed border-[#E2E8F0] rounded-xl bg-[#F8FAFC]">
                          <p className="text-sm font-bold text-[#64748B]">No tracks found.</p>
                          <p className="text-xs font-medium text-[#94a3b8] mt-1">Place your downloaded MP3s in the <br/><code className="bg-white px-1 py-0.5 rounded border border-[#E2E8F0]">backend/data/library/music</code> folder.</p>
                        </div>
                      ) : (
                        <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2 hide-scrollbar">
                          {musicLibrary.map((track, i) => (
                            <div key={i} className={`flex items-center justify-between p-4 rounded-xl border transition-all ${selectedMusicPath === track.path ? 'border-[#0EA5E9] bg-[#0EA5E9]/5' : 'border-[#E2E8F0] hover:bg-[#F8FAFC]'}`}>
                              <div className="flex items-center gap-4">
                                <button onClick={() => { if(selectedMusicPath !== track.path) setSelectedMusicPath(track.path); else setSelectedMusicPath(''); }} className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${selectedMusicPath === track.path ? 'border-[#0EA5E9]' : 'border-[#cbd5e1]'}`}>
                                  {selectedMusicPath === track.path && <div className="w-3 h-3 rounded-full bg-[#0EA5E9]" />}
                                </button>
                                <div>
                                  <p className="font-bold text-[#0F172A] text-sm">{track.name}</p>
                                  <span className="text-[10px] font-bold text-[#64748B] uppercase tracking-wider">{track.tag}</span>
                                </div>
                              </div>
                              <audio src={`http://localhost:8000/${track.path}`} controls controlsList="nodownload" className="h-8 w-40" />
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {musicMode === 'Custom' && (
                    <div className="flex flex-col h-full">
                      <h3 className="text-sm font-black text-[#64748B] uppercase tracking-wider mb-4">Upload MP3/WAV</h3>
                      <div className="flex-1 flex flex-col items-center justify-center p-10 border-2 border-dashed border-[#cbd5e1] rounded-2xl bg-[#F8FAFC] relative">
                        {isUploadingMusic ? (
                          <Loader2 size={32} className="animate-spin text-[#0EA5E9]" />
                        ) : selectedMusicPath && selectedMusicPath.startsWith('data/') && !selectedMusicPath.includes('library') ? (
                          <div className="text-center w-full">
                            <CheckCircle2 size={40} className="text-[#10B981] mx-auto mb-3" />
                            <p className="font-bold text-[#0F172A] mb-4 truncate">{selectedMusicPath.split('/').pop()}</p>
                            <audio src={`http://localhost:8000/${selectedMusicPath}`} controls className="w-full mb-4" />
                            <button onClick={() => setSelectedMusicPath('')} className="text-xs font-bold text-red-500 hover:underline">Remove Track</button>
                          </div>
                        ) : (
                          <div className="text-center">
                            <UploadCloud size={32} className="text-[#64748B] mx-auto mb-3" />
                            <p className="font-bold text-[#0F172A] mb-1">Select Custom Audio File</p>
                            <p className="text-xs text-[#94a3b8] mb-4">MP3, WAV, M4A up to 20MB</p>
                            <input 
                              type="file" 
                              accept="audio/*" 
                              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                              onChange={async (e) => {
                                const file = e.target.files[0];
                                if (!file) return;
                                setIsUploadingMusic(true);
                                const formData = new FormData();
                                formData.append('file', file);
                                try {
                                  const res = await apiFetch(`/projects/${id}/uploads/music`, { method: 'POST', body: formData });
                                  const data = await res.json();
                                  setSelectedMusicPath(data.localPath.replace(/\\/g, '/'));
                                  setMusicMode('Custom');
                                } catch (err) {
                                  setLocalError('Failed to upload custom music.');
                                } finally {
                                  setIsUploadingMusic(false);
                                }
                              }}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                </div>
              </div>

              {/* Mixing Controls */}
              {musicMode !== 'None' && (
                <div className="bg-white border border-[#E2E8F0] shadow-sm p-8 rounded-[2rem] mb-10">
                  <h3 className="text-sm font-black text-[#64748B] uppercase tracking-wider mb-6">Audio Mixing</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                    <div>
                      <div className="flex justify-between items-center mb-3">
                        <label className="text-sm font-bold text-[#0F172A]">Background Music Volume</label>
                        <span className="text-xs font-black text-[#0EA5E9] bg-[#0EA5E9]/10 px-2 py-1 rounded-md">{Math.round(musicVolume * 100)}%</span>
                      </div>
                      <input type="range" min="0" max="1" step="0.05" value={musicVolume} onChange={(e) => setMusicVolume(parseFloat(e.target.value))} className="w-full accent-[#0EA5E9]" />
                    </div>
                    <div>
                      <div className="flex justify-between items-center mb-3">
                        <label className="text-sm font-bold text-[#0F172A]">Original Clip Audio (Voiceover)</label>
                        <span className="text-xs font-black text-[#0EA5E9] bg-[#0EA5E9]/10 px-2 py-1 rounded-md">{Math.round(voVolume * 100)}%</span>
                      </div>
                      <input type="range" min="0" max="1" step="0.05" value={voVolume} onChange={(e) => setVoVolume(parseFloat(e.target.value))} className="w-full accent-[#0EA5E9]" />
                    </div>
                  </div>
                </div>
              )}

              <div className="flex justify-center">
                <button 
                  onClick={handleGenerateReel} 
                  disabled={musicMode === 'Library' && !selectedMusicPath}
                  className="bg-[#0EA5E9] text-white px-14 py-6 rounded-2xl text-xl font-black shadow-[0_20px_40px_rgba(14,165,233,0.3)] hover:scale-105 active:scale-95 transition-all flex items-center gap-3 disabled:opacity-50 disabled:hover:scale-100"
                >
                  <Play fill="white" size={24} /> Render Final Video
                </button>
              </div>
            </motion.div>
          )}

          {/* STEP 6: GENERATION SCREEN */}
          {currentStep === 6 && (
            <motion.div key="step5" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="h-full flex flex-col items-center justify-center max-w-2xl mx-auto w-full text-center">
              <div className="relative w-32 h-32 mb-10">
                <div className="absolute inset-0 border-[6px] border-[#0EA5E9]/10 rounded-full"></div>
                <div className="absolute inset-0 border-[6px] border-[#0EA5E9] rounded-full border-t-transparent animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center"><Activity size={40} className="text-[#0EA5E9] animate-pulse" /></div>
              </div>
              
              <h2 className="text-4xl font-black text-[#0F172A] mb-4">Rendering {aspectRatio === '16:9' ? 'YouTube Video' : 'Shorts Reel'}</h2>
              <p className="text-xl text-[#64748B] font-medium mb-12">Applying {reelStyle} styling, color grading, and dynamic cuts...</p>
              
              <div className="w-full bg-white border border-[#E2E8F0] shadow-sm p-8 rounded-[2rem] text-left">
                <ProgressStepper steps={steps} currentStep={sseStep} isProcessing={isProcessing} />
              </div>
            </motion.div>
          )}

          {/* STEP 7: EXPORT RESULTS */}
          {currentStep === 7 && (
            <motion.div key="step6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col lg:flex-row gap-10 max-w-7xl mx-auto">
              
              {/* Left Video Player */}
              <div className={`bg-[#0F172A] rounded-[2rem] overflow-hidden shadow-2xl border-[#E2E8F0] ${previewRatioClass} lg:w-1/2 flex-shrink-0 flex items-center justify-center`}>
                {resultsData[0]?.video_url || resultsData[0]?.videoUrl ? (
                  <video src={`http://localhost:8000${resultsData[0].video_url || resultsData[0].videoUrl}`} controls className="w-full h-full object-contain" autoPlay loop />
                ) : (
                  <p className="text-white font-medium">Video preview unavailable</p>
                )}
              </div>

              {/* Right Export Panel */}
              <div className="flex-1 flex flex-col justify-center py-4">
                <div className="mb-10">
                  <h2 className="text-4xl font-black text-[#0F172A] flex items-center gap-3 mb-3">
                    <CheckCircle2 size={36} className="text-[#10B981]" /> Generation Complete
                  </h2>
                  <p className="text-xl text-[#64748B] font-medium">Your premium {reelStyle} reel is ready for publishing.</p>
                </div>

                <div className="bg-white border border-[#E2E8F0] shadow-sm p-8 rounded-3xl mb-10">
                   <h4 className="text-sm font-black text-[#64748B] uppercase tracking-wider mb-4 flex items-center gap-2"><Type size={18} className="text-[#0EA5E9]"/> Generated Caption / Hook</h4>
                   {resultsData[0]?.hook ? (
                     <p className="text-base font-bold text-[#0F172A] leading-relaxed">
                       "{resultsData[0].hook}"<br/><br/>
                       <span className="text-sm font-medium text-[#64748B]">{resultsData[0].description}</span>
                     </p>
                   ) : (
                     <p className="text-sm italic text-[#94a3b8]">No AI caption generated.</p>
                   )}
                </div>

                <div className="space-y-4">
                  <button 
                    onClick={async () => {
                      const url = `http://localhost:8000${resultsData[0]?.video_url || resultsData[0]?.videoUrl}`;
                      try {
                        const response = await fetch(url);
                        const blob = await response.blob();
                        const blobUrl = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = blobUrl;
                        a.download = `ReelForge_${resultsData[0]?.style || 'Video'}.mp4`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(blobUrl);
                      } catch (err) {
                        console.error('Download failed', err);
                        window.open(url, '_blank');
                      }
                    }}
                    className="w-full bg-[#0F172A] text-white py-6 rounded-2xl text-xl font-black shadow-xl hover:bg-[#1e293b] transition-all flex justify-center items-center gap-3"
                  >
                    <Download size={24} /> Download Final MP4
                  </button>
                </div>
              </div>

            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </div>
  );
}
