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
  const abortRef = useRef(null);

  const handlePayload = useCallback((payload) => {
    let data;
    try {
      data = JSON.parse(payload);
    } catch {
      return;
    }

    if (data.status === 'progress') {
      setProgressLog((prev) => [...prev, data.message]);

      const step = matchStep(data.message || '');
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
      setIsProcessing(false);
      setSteps((prev) => prev.map((s) => ({ ...s, status: 'done' })));
    } else if (data.status === 'error') {
      setError(data.message || 'Processing failed.');
      setIsProcessing(false);
    }
  }, []);

  const start = useCallback((url, options = {}) => {
    const token = options.token;
    setIsProcessing(true);
    setProgressLog([]);
    setSteps([]);
    setCurrentStep(null);
    setResult(null);
    setError('');

    if (abortRef.current) {
      abortRef.current.abort();
    }

    const controller = new AbortController();
    abortRef.current = controller;

    const parseChunk = (buffer) => {
      const events = [];
      const parts = buffer.split(/\r?\n\r?\n/);
      const remainder = parts.pop() || '';

      for (const block of parts) {
        const lines = block.split(/\r?\n/);
        const payload = lines
          .filter((line) => line.startsWith('data:'))
          .map((line) => line.slice(5).trimStart())
          .join('\n');
        if (payload) {
          events.push(payload);
        }
      }

      return { events, remainder };
    };

    (async () => {
      try {
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const response = await fetch(url, {
          method: 'GET',
          headers,
          signal: controller.signal,
          cache: 'no-store',
        });

        if (!response.ok || !response.body) {
          throw new Error(`SSE request failed (${response.status})`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const { events, remainder } = parseChunk(buffer);
          buffer = remainder;

          for (const payload of events) {
            handlePayload(payload);
          }
        }
      } catch {
        if (controller.signal.aborted) return;
        setError('Lost connection to processing server.');
        setIsProcessing(false);
      } finally {
        if (abortRef.current === controller) {
          abortRef.current = null;
        }
      }
    })();
  }, [handlePayload]);

  const cancel = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
      setIsProcessing(false);
    }
  }, []);

  return { isProcessing, progressLog, steps, currentStep, result, error, start, cancel };
}
