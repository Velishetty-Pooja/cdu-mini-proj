import { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { VideoJobStatus, VideoJobResult } from '../types';

export function useAnalysisJob(jobId: string | null) {
  const [status, setStatus] = useState<'queued' | 'processing' | 'completed' | 'failed' | 'idle'>('idle');
  const [progress, setProgress] = useState<number>(0);
  const [message, setMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VideoJobResult | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(false);

  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!jobId) {
      setStatus('idle');
      setProgress(0);
      setMessage('');
      setError(null);
      setResult(null);
      setIsPolling(false);
      return;
    }

    setIsPolling(true);
    setStatus('queued');
    setProgress(0);
    setMessage('Queued for processing...');
    setError(null);

    const poll = async () => {
      try {
        const jobStatus: VideoJobStatus = await api.getJobStatus(jobId);
        setStatus(jobStatus.status);
        setProgress(jobStatus.progress_percent);
        setMessage(jobStatus.message);

        if (jobStatus.status === 'completed') {
          setResult(jobStatus.result || null);
          setIsPolling(false);
          return;
        }

        if (jobStatus.status === 'failed') {
          setError(jobStatus.error || 'Video analysis failed.');
          setIsPolling(false);
          return;
        }

        // Keep polling if queued or processing
        timerRef.current = window.setTimeout(poll, 1200);
      } catch (err: any) {
        console.error('Polling error:', err);
        setError(err.response?.data?.detail || err.message || 'Error checking job status');
        // Retry a couple times or back off
        timerRef.current = window.setTimeout(poll, 2500);
      }
    };

    poll();

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [jobId]);

  return {
    status,
    progress,
    message,
    error,
    result,
    isPolling,
  };
}
