import React, { useState, useEffect } from 'react';
import {
  Upload,
  Film,
  Image as ImageIcon,
  CheckCircle,
  AlertCircle,
  Play,
  FileCode,
  Loader2,
} from 'lucide-react';
import { ConfigDrawer } from '../components/ConfigDrawer';
import { api } from '../services/api';
import { useAnalysisJob } from '../hooks/useAnalysisJob';
import {
  SampleMedia,
  LaneDefinition,
  CountingLineDefinition,
  ImageAnalysisResponse,
} from '../types';

interface UploadPageProps {
  onAnalysisComplete: (analysisId: string, resultData: any) => void;
}

export const UploadPage: React.FC<UploadPageProps> = ({ onAnalysisComplete }) => {
  const [activeTab, setActiveTab] = useState<'upload' | 'samples'>('upload');
  const [mediaType, setMediaType] = useState<'image' | 'video'>('video');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Configuration options
  const [confidence, setConfidence] = useState<number>(0.25);
  const [sampleStride, setSampleStride] = useState<number>(2);
  const [direction, setDirection] = useState<string>('down');
  const [roadRoi, setRoadRoi] = useState<number[] | null>(null);
  const [lanes, setLanes] = useState<LaneDefinition[]>([]);
  const [countingLines, setCountingLines] = useState<CountingLineDefinition[]>([]);

  // Video background job polling state
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const { status: jobStatus, progress: jobProgress, message: jobMessage, error: jobError, result: jobResult } = useAnalysisJob(activeJobId);

  // Sample media list
  const [samples, setSamples] = useState<SampleMedia[]>([]);

  useEffect(() => {
    api.getSampleMedia()
      .then((data) => setSamples(data.samples || []))
      .catch((err) => console.error('Failed to load sample media:', err));
  }, []);

  // When video job finishes, trigger callback
  useEffect(() => {
    if (jobStatus === 'completed' && jobResult && activeJobId) {
      onAnalysisComplete(activeJobId, jobResult);
    }
  }, [jobStatus, jobResult, activeJobId, onAnalysisComplete]);

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      const isVid = file.type.startsWith('video/') || file.name.match(/\.(mp4|avi|mov|mkv)$/i);
      setMediaType(isVid ? 'video' : 'image');
      setSelectedFile(file);
      setUploadError(null);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      const isVid = file.type.startsWith('video/') || file.name.match(/\.(mp4|avi|mov|mkv)$/i);
      setMediaType(isVid ? 'video' : 'image');
      setSelectedFile(file);
      setUploadError(null);
    }
  };

  const startAnalysis = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadError(null);
    setActiveJobId(null);

    const configOpts = {
      confidence,
      sampleStride,
      direction,
      roadRoi: roadRoi || undefined,
      lanes,
      countingLines,
    };

    try {
      if (mediaType === 'image') {
        const response: ImageAnalysisResponse = await api.analyzeImage(selectedFile, configOpts);
        setIsUploading(false);
        onAnalysisComplete(response.analysis_id, response);
      } else {
        const job = await api.analyzeVideo(selectedFile, configOpts);
        setIsUploading(false);
        setActiveJobId(job.job_id); // Initiates real polling
      }
    } catch (err: any) {
      setIsUploading(false);
      setUploadError(err.response?.data?.detail || err.message || 'Analysis request failed.');
    }
  };

  const runSample = async (sampleName: string, isVideo: boolean) => {
    setIsUploading(true);
    setUploadError(null);
    setActiveJobId(null);

    const configOpts = {
      confidence,
      sampleStride,
      direction,
      roadRoi: roadRoi || undefined,
      lanes,
      countingLines,
    };

    try {
      const res = await api.analyzeSampleMedia(sampleName, configOpts);
      setIsUploading(false);
      if (isVideo) {
        setActiveJobId(res.job_id);
      } else {
        onAnalysisComplete(res.analysis_id, res);
      }
    } catch (err: any) {
      setIsUploading(false);
      setUploadError(err.response?.data?.detail || err.message || 'Sample execution failed.');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-1">
        <h1 className="text-2xl font-extrabold text-white tracking-tight">
          Traffic Media Ingestion & Analysis
        </h1>
        <p className="text-xs text-slate-400">
          Upload local images or video footage to perform real YOLO vehicle detection and direction tracking.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex justify-center">
        <div className="bg-slate-900 p-1 rounded-xl border border-slate-800 flex space-x-1">
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'upload' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Upload Media File
          </button>
          <button
            onClick={() => setActiveTab('samples')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'samples' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Pre-Packaged Samples ({samples.length})
          </button>
        </div>
      </div>

      {activeTab === 'upload' ? (
        <div className="space-y-6">
          {/* Dropzone */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            className="border-2 border-dashed border-slate-700 hover:border-cyan-500/80 bg-slate-900/50 hover:bg-slate-900 p-8 rounded-2xl text-center cursor-pointer transition-all"
          >
            <input
              type="file"
              id="file-input"
              accept="image/*,video/*"
              onChange={handleFileSelect}
              className="hidden"
            />
            <label htmlFor="file-input" className="cursor-pointer space-y-3 block">
              <div className="w-14 h-14 rounded-2xl bg-cyan-950/60 border border-cyan-800 flex items-center justify-center mx-auto text-cyan-400 shadow-lg">
                <Upload className="w-7 h-7" />
              </div>
              <div>
                <span className="text-sm font-bold text-white">Click to browse</span>
                <span className="text-xs text-slate-400"> or drag and drop footage here</span>
              </div>
              <p className="text-[11px] text-slate-500">
                Supports MP4, AVI, MOV, MKV (Videos up to 150MB) and JPG, PNG, WEBP (Images up to 25MB)
              </p>
            </label>
          </div>

          {/* Selected File Banner */}
          {selectedFile && (
            <div className="flex items-center justify-between p-3.5 bg-slate-900 border border-slate-800 rounded-xl">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${mediaType === 'video' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-amber-500/20 text-amber-400'}`}>
                  {mediaType === 'video' ? <Film className="w-5 h-5" /> : <ImageIcon className="w-5 h-5" />}
                </div>
                <div>
                  <div className="text-xs font-bold text-white truncate max-w-sm">{selectedFile.name}</div>
                  <div className="text-[11px] text-slate-400">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {mediaType.toUpperCase()}
                  </div>
                </div>
              </div>

              <button
                onClick={() => setSelectedFile(null)}
                className="text-xs text-slate-500 hover:text-rose-400 font-medium"
              >
                Remove
              </button>
            </div>
          )}

          {/* Configuration Controls */}
          <ConfigDrawer
            confidence={confidence}
            onConfidenceChange={setConfidence}
            sampleStride={sampleStride}
            onSampleStrideChange={setSampleStride}
            direction={direction}
            onDirectionChange={setDirection}
            roadRoi={roadRoi}
            onRoadRoiChange={setRoadRoi}
            lanes={lanes}
            onLanesChange={setLanes}
            countingLines={countingLines}
            onCountingLinesChange={setCountingLines}
          />

          {/* Error Message */}
          {(uploadError || jobError) && (
            <div className="p-3.5 bg-rose-950/60 border border-rose-800 rounded-xl flex items-start space-x-2.5 text-xs text-rose-300">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{uploadError || jobError}</span>
            </div>
          )}

          {/* Video Processing Progress Card */}
          {activeJobId && (
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                  <span className="text-xs font-bold text-white">Video Analysis in Progress...</span>
                </div>
                <span className="text-xs font-bold text-cyan-400">{jobProgress}%</span>
              </div>

              <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                <div
                  className="bg-cyan-500 h-full rounded-full transition-all duration-300"
                  style={{ width: `${jobProgress}%` }}
                />
              </div>

              <p className="text-xs text-slate-400">{jobMessage || 'Processing video frames...'}</p>
            </div>
          )}

          {/* Submit Action */}
          <button
            onClick={startAnalysis}
            disabled={!selectedFile || isUploading || activeJobId !== null}
            className={`w-full py-3 rounded-xl text-xs font-bold transition-all shadow-lg flex items-center justify-center space-x-2 ${
              !selectedFile || isUploading || activeJobId !== null
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-600/25 cursor-pointer'
            }`}
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Uploading & Initializing...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Start Traffic Analysis</span>
              </>
            )}
          </button>
        </div>
      ) : (
        /* Samples Tab */
        <div className="space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl text-xs text-slate-300">
            Select a verified sample file from local storage to immediately test detection, ByteTrack multi-object tracking, and direction analysis.
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {samples.map((s) => (
              <div
                key={s.name}
                className="bg-slate-900 border border-slate-800 hover:border-slate-700 p-4 rounded-xl flex items-center justify-between transition-all"
              >
                <div className="flex items-center space-x-3">
                  <div className={`p-2.5 rounded-lg ${s.type === 'video' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-amber-500/20 text-amber-400'}`}>
                    {s.type === 'video' ? <Film className="w-5 h-5" /> : <ImageIcon className="w-5 h-5" />}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white">{s.name}</div>
                    <div className="text-[11px] text-slate-400">
                      {(s.size_bytes / (1024 * 1024)).toFixed(2)} MB • {s.type.toUpperCase()}
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => runSample(s.name, s.type === 'video')}
                  disabled={isUploading || activeJobId !== null}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-cyan-600 text-cyan-300 hover:text-white text-xs font-semibold transition-colors"
                >
                  Run Test
                </button>
              </div>
            ))}
          </div>

          {/* Active Job status for sample runs */}
          {activeJobId && (
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3 mt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                  <span className="text-xs font-bold text-white">Sample Video Analysis in Progress...</span>
                </div>
                <span className="text-xs font-bold text-cyan-400">{jobProgress}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                <div className="bg-cyan-500 h-full rounded-full transition-all" style={{ width: `${jobProgress}%` }} />
              </div>
              <p className="text-xs text-slate-400">{jobMessage}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
