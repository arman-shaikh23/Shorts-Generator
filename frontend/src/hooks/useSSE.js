import { useState, useCallback, useRef } from 'react';

const STEP_MAP = [
  { match: 'Downloading', label: 'Uploading', icon: '↑', description: 'Fetching your clips' },
  { match: 'Uploading Clips', label: 'Uploading', icon: '↑', description: 'Sending to AI' },
  { match: 'Detecting Scenes', label: 'Analyzing', icon: '🔍', description: 'AI scanning footage' },
  { match: 'Classifying', label: 'Classifying', icon: '🏠', description: 'Identifying rooms' },
  { match: 'Ranking', label: 'Scoring', icon: '⭐', description: 'Rating clip quality' },
  { match: 'Building Story', label: 'Story Building', icon: '📖', description: 'Creating walkthrough' },
  { match: 'Generating Reel', label: 'Rendering', icon: '🎬', description: 'FFmpeg export' },
  { match: 'Exporting', label: 'Finalizing', icon: '✅', description: 'Packaging for download' },
];

function matchStep(message) {
  for (const step of STEP_MAP) {
    if (message.includes(step.match)) return step;
  }
  return null;
}

export function useSSE() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressLog, setProgressLog] = useState([]);
  const [steps, setSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const sseRef = useRef(null);

  const start = useCallback((url) => {
    setIsProcessing(true);
    setProgressLog([]);
    setSteps([]);
    setCurrentStep(null);
    setResult(null);
    setError('');

    const sse = new EventSource(url);
    sseRef.current = sse;

    sse.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.status === 'progress') {
        setProgressLog((prev) => [...prev, data.message]);

        const step = matchStep(data.message);
        if (step) {
          setCurrentStep(step);
          setSteps((prev) => {
            const exists = prev.find((s) => s.label === step.label);
            if (exists) return prev;
            return [...prev, { ...step, status: 'active' }];
          });
        }
      } else if (data.status === 'completed') {
        setResult(data);
        sse.close();
        setIsProcessing(false);
        setSteps((prev) => prev.map((s) => ({ ...s, status: 'done' })));
      } else if (data.status === 'error') {
        setError(data.message);
        sse.close();
        setIsProcessing(false);
      }
    };

    sse.onerror = () => {
      setError('Lost connection to processing server.');
      sse.close();
      setIsProcessing(false);
    };
  }, []);

  const cancel = useCallback(() => {
    if (sseRef.current) {
      sseRef.current.close();
      setIsProcessing(false);
    }
  }, []);

  return { isProcessing, progressLog, steps, currentStep, result, error, start, cancel };
}
