import { useState } from 'react';

function App() {
  const [videoUrl, setVideoUrl] = useState('');
  const [propertyName, setPropertyName] = useState('');
  
  const [status, setStatus] = useState('idle'); // idle | processing | completed | error
  const [message, setMessage] = useState('');
  const [results, setResults] = useState([]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!videoUrl || !propertyName) return;
    
    setStatus('processing');
    setMessage('Connecting to AI Engine...');
    setResults([]);
    
    // Use relative URL in production since we serve static from FastAPI
    const baseUrl = import.meta.env.DEV ? "http://localhost:8000" : "";
    const url = `${baseUrl}/api/process?video_url=${encodeURIComponent(videoUrl)}&property_name=${encodeURIComponent(propertyName)}`;
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
              <label>Dropbox Video URL</label>
              <input 
                type="url" 
                placeholder="https://www.dropbox.com/..." 
                value={videoUrl}
                onChange={(e) => setVideoUrl(e.target.value)}
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
              <div key={index} className="glass-card result-card">
                <div className="video-container">
                  <video src={`${import.meta.env.DEV ? "http://localhost:8000" : ""}${item.video_url}`} controls autoPlay muted loop playsInline />
                </div>
                
                <div className="result-meta">
                  <h3 className="result-title">{item.title}</h3>
                  <div className="result-script">
                    <strong>Suggested Caption:</strong><br/>
                    {item.script}
                  </div>
                  <div className="result-hashtags">
                    {item.hashtags && item.hashtags.join(' ')}
                  </div>
                  <a 
                    href={`${import.meta.env.DEV ? "http://localhost:8000" : ""}${item.video_url}`} 
                    download={`short_${index + 1}.mp4`} 
                    className="btn-download"
                    target="_blank"
                    rel="noreferrer"
                  >
                    <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="7 10 12 15 17 10"></polyline>
                      <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Download Clip
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
