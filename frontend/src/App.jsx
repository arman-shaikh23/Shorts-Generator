import { useState } from 'react';

function App() {
  const [videoUrls, setVideoUrls] = useState('');
  const [propertyName, setPropertyName] = useState('');
  
  const [status, setStatus] = useState('idle'); // idle | processing | completed | error
  const [message, setMessage] = useState('');
  const [results, setResults] = useState([]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    const urls = videoUrls.split('\n').map(u => u.trim()).filter(u => u.length > 0);
    if (urls.length < 5 || urls.length > 10) {
      setMessage(`Please provide between 5 and 10 URLs. You provided ${urls.length}.`);
      setStatus('error');
      return;
    }
    if (!propertyName) return;
    
    setStatus('processing');
    setMessage('Connecting to AI Engine...');
    setResults([]);
    
    // Use relative URL in production since we serve static from FastAPI
    const baseUrl = import.meta.env.DEV ? "http://localhost:8000" : "";
    const urlParams = urls.map(u => `video_url=${encodeURIComponent(u)}`).join('&');
    const url = `${baseUrl}/api/process?${urlParams}&property_name=${encodeURIComponent(propertyName)}`;
    const eventSource = new EventSource(url);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.status === 'progress') {
          setMessage(data.message);
        } else if (data.status === 'completed') {
          setResults(data.results);
          setStatus('completed');
          eventSource.close();
        } else if (data.status === 'error') {
          setMessage(`Error: ${data.message}`);
          setStatus('error');
          eventSource.close();
        }
      } catch (err) {
        console.error("Failed to parse SSE data", err);
      }
    };
    
    eventSource.onerror = () => {
      setMessage("Connection lost. Please try again.");
      setStatus('error');
      eventSource.close();
    };
  };

  return (
    <div className="container">
      <h1>Groovy Shorts Gen</h1>
      <p className="subtitle">AI-powered property video to viral shorts converter</p>
      
      {status === 'idle' || status === 'error' ? (
        <div className="glass-card">
          <form onSubmit={handleSubmit} className="input-group">
            <div className="input-field">
              <label>Dropbox Video URLs (5-10 links, one per line)</label>
              <textarea 
                placeholder="https://www.dropbox.com/...&#10;https://www.dropbox.com/..." 
                value={videoUrls}
                onChange={(e) => setVideoUrls(e.target.value)}
                rows={6}
                required
              />
            </div>
            
            <div className="input-field">
              <label>Property Name</label>
              <input 
                type="text" 
                placeholder="e.g. Ambrose — Luxury Apartments, Dallas TX" 
                value={propertyName}
                onChange={(e) => setPropertyName(e.target.value)}
                required
              />
            </div>
            
            {status === 'error' && (
              <div style={{ color: '#ef4444', background: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '8px' }}>
                {message}
              </div>
            )}
            
            <button type="submit" className="btn-primary">
              Generate Shorts ✨
            </button>
          </form>
        </div>
      ) : null}

      {status === 'processing' && (
        <div className="glass-card progress-container">
          <div className="progress-loader"></div>
          <p className="progress-text">{message}</p>
        </div>
      )}

      {status === 'completed' && (
        <div className="results-container">
          <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>Ready to Publish 🎉</h2>
          <div className="results-grid">
            {results.map((item, index) => (
              <div key={index} className="glass-card result-card" style={{ maxWidth: '600px', margin: '0 auto' }}>
                <div className="video-container">
                  <video src={`${import.meta.env.DEV ? "http://localhost:8000" : ""}${item.video_url}`} controls autoPlay muted loop playsInline />
                </div>
                
                <div className="result-meta">
                  <h3 className="result-title">{item.title}</h3>
                  <div className="result-script">
                    <strong>Hook:</strong> {item.hook}<br/><br/>
                    <strong>Total Duration:</strong> {item.total_duration || "20-30s"}<br/>
                    <strong>Scenes Used:</strong> {item.selected_scenes?.length || 0}
                  </div>
                  <div className="result-hashtags" style={{ marginTop: '1rem', color: '#3b82f6', fontWeight: '500' }}>
                    {item.hashtags && item.hashtags.map(tag => tag.startsWith('#') ? tag : `#${tag}`).join(' ')}
                  </div>
                  <a 
                    href={`${import.meta.env.DEV ? "http://localhost:8000" : ""}${item.video_url}`} 
                    download={`final_reel.mp4`} 
                    className="btn-download"
                    target="_blank"
                    rel="noreferrer"
                    style={{ marginTop: '1.5rem' }}
                  >
                    <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="7 10 12 15 17 10"></polyline>
                      <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Download Reel
                  </a>
                </div>
              </div>
            ))}
          </div>
          <div style={{ textAlign: 'center', marginTop: '3rem' }}>
            <button onClick={() => setStatus('idle')} className="btn-primary" style={{ width: 'auto' }}>
              Create More Shorts
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
